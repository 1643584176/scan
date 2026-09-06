# Figma AI Thread Livegraph Access - Investigation Notes

Date: 2026-09-06
Scope: www.figma.com livegraph (in-scope). Accounts A(1643 victim-view) / B(7294 attacker-view), both user-owned.

## Views confirmed live (server registry, via bundle `o(name, argKeys, hash)` registration)

| View | argKeys | viewHash |
|---|---|---|
| FileAiChatThreadsView | ownerId (= fileKey in practice) | 3ebe8bcd1ab2477b47769f9f4463b6541a104b6d6762402c7ffadd514bfbe08c |
| ActiveAiChatThreadView | id, ownerId | c3da192046fd45ef6a25d70977aebce1af33d5be14bd5baddb70a55e84a7d048 |
| ActiveAiChatThreadPaginatedView | firstPageSize, id, ownerId | c34678cace0a64e9cab06dbe5732a18cea1fcfb7b7c76cab5ac7a1320699d3cc |
| PaginatedUserAiChatThreadsView | firstPageSize, ownerId, userId | 2818b3f2a36280603a83950594beba37f9a0bfe0ad59cfbf00889ac2a8d49748 |
| NodeAiChatThreadsBySessionView | externalSessionId, nodeGuid, ownerId | 864982e9ae7f91f2510404440c3ad72050b9887ad550dbf15ba05d3413f16502 |
| AiChatThreadMessageCountView | id, ownerId | 69d4ed43ab3c4dec7abd2c3437c3bceae50ccc3ed0fdd08d859c54c13d5ac096 |
| AiAssistantKillSwitchView | [] | 01a5350a5d6b49eb45aa04414b294f5a815be998b73ea80a7bb3de567299b928 |

## Findings (B identity, cookie COOKIE_B, auth userId=UID_B)

1. FileAiChatThreadsView {ownerId: FILE_A} -> returns A's AI thread(s) fully:
   - thread a2f71e01-40c9-4439-9438-e89b23942c21, privacyMode="file", userId=UID_A(owner),
     title "Design next user screen", previewNodeGuid 1:806, threadType assistant, 18 messages, created 2026-09-02
   - includes latestUserMessage content parts (user text + base64 png selected-nodes snapshot)
   - BASE-B (ownerId: FILE_B) -> empty (B file has no threads) => view functional, result is real data not artifact

2. ActiveAiChatThreadView / ActiveAiChatThreadPaginatedView {id: <threadId>, ownerId: FILE_A} -> FULL thread history:
   - all messages (user/assistant/tool roles), AI reply text parts with <figma-node-link>, reasoning parts,
     tool-result-json parts (internal mcp plugin ids), selected-nodes png snapshots, user gravatar
   - => B (viewer of FILE_A) can read every part of A's shared thread

3. PaginatedUserAiChatThreadsView {firstPageSize, ownerId: UID_A, userId: UID_A} -> empty
   (A has no user-level/home threads; thread is file-scoped)

4. Public file (ucha7bf05fJ81CJZVoruo0 Flowbite) FileAiChatThreadsView -> empty (no threads exist there)

## Product semantics (from JS bundles)

- Thread privacyMode enum: "user" (private) / "file" (shared to file)
  - New AI Assistant chat is created with privacyMode:"user" (analytics event ai_assistant.new_chat_created, chunk 0c62c2fd)
  - code_chat duplicated threads get privacyMode:"file" (chunk 8049)
- UI badges (chunk 2688, feature gate ai_assistant_sharing):
  - privacyMode FILE -> i18n key ai_assistant.chat.thread_privacy_shared ("shared" badge)
  - privacyMode USER -> i18n key ai_assistant.chat.history.private_badge ("private" badge)
- ThreadsManager (main bundle) loads ALL fileAiChatThreads into store without client-side userId filter;
  UI visibility relies on privacyMode + ai_assistant_sharing gate
- A's thread is privacyMode="file" => it was explicitly/flow-shared to file scope => B seeing it is likely BY DESIGN

## Open question / next experiment (control test)

Does the server filter privacyMode="user" threads on FileAiChatThreadsView / ActiveAiChatThreadView?

Plan:
1. User (account A) creates a NEW Ask Figma thread in FILE_A via UI, asks one question, does NOT share it
   (expected server state privacyMode="user")
2. Probe with B identity: FileAiChatThreadsView {ownerId: FILE_A} and ActiveAiChatThreadView
   {id: <new threadId>, ownerId: FILE_A}
3. If B can see/read the "user" thread -> server ignores privacyMode => real IDOR (CWE-639),
   private AI conversation disclosure to any file viewer. If hidden -> filter works; line closed.

## Request budget / rate discipline

- WS probes: 6 connections total so far (2x probe1, 1x probe2, 3x scope), all authSuccess, no 202/rate-limit
- Keep UA full, 1-2s gaps, stop on any 202/error
