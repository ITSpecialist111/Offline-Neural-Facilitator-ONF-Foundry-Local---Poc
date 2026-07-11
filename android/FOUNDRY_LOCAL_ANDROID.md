# Foundry Local Android integration decision

Status: **preview-ready, awaiting official client SDK access**<br>
Reviewed: 2026-07-11

## Evidence

Microsoft announced Foundry Local for Android on November 20, 2025:

- <https://devblogs.microsoft.com/foundry/foundry-local-comes-to-android/>
- gated preview enrollment: <https://aka.ms/foundrylocal-androidprp>
- Play companion: <https://play.google.com/store/apps/details?id=com.microsoft.foundrylocal.app>
- preview license: <https://learn.microsoft.com/legal/foundry-local/microsoft-foundry-local-android-license-terms>

The announcement describes on-device chat and Whisper transcription, hardware-aware model selection, self-contained packaging, OpenAI-style requests/responses, and an Android SDK. The Play listing identifies the installed application as a companion service for client apps and advertises modern Kotlin APIs, audio support, and automatic model-catalog routing.

## Verified on the Fold7

The official Play package is installed on the physical Samsung Fold7:

| Property | Value |
|---|---|
| Package | `com.microsoft.foundrylocal.app` |
| Version | `0.1.5` (`1050`) |
| Android range | API 33 minimum, API 35 target |
| ABI | `arm64-v8a` |
| Distribution | Google Play, Microsoft-signed |
| Companion service | Exported `FoundryLocalService` in a dedicated process |
| Client bootstrap | Internal IPC initialization provider |
| Network | Companion declares `INTERNET` and network-state permissions |

The Foundry UI explicitly states that mobile developers need the Foundry Local Android SDK. Its developer link opens the gated preview enrollment form.

## Availability boundary

The Android client artifact is not currently published on Maven Central or Google Maven. Public Foundry Local source and Learn documentation expose C#, JavaScript, Python, Rust, and C++ samples, but not the gated Android Kotlin package.

The installed companion contains the service implementation and IPC surface, but ONF will not copy classes from its APK, derive a private Binder contract, or call undocumented interfaces. That would be unsupported, fragile, and inconsistent with the preview license.

## Runtime decision

ONF already defines a pluggable `LocalLlmEngine`. The runtime order is:

1. **Foundry Local Android engine** — preferred once the official Kotlin client SDK is granted.
2. **LiteRT-LM Gemma engine** — current, fully functional fallback.
3. **Deterministic ONF core** — sessions, RAG, skills, decisions, actions, and exports remain usable without either model runtime.

The application detects the official companion package and reports its version in the Private System sheet. Detection grants no access to companion data and adds no network permission.

## Implemented runtime chooser

The Private System sheet now makes the boundary visible instead of hiding it behind automatic fallback:

- ONF retains every successfully imported `.litertlm` pack in its own private model library;
- users can switch between E2B, E4B, and future compatible LiteRT-LM packs without deleting the previous model;
- deletion is explicit and the active model cannot be removed accidentally;
- a failed model load attempts to restore the prior engine;
- the official Foundry companion version is shown separately with **Open companion** and **Request SDK access** actions;
- Foundry catalog selection remains unavailable until the documented Kotlin client package is linked.

The current runtime is LiteRT-LM or deterministic ONF. Companion detection alone is not represented as an active Foundry runtime.

## Cross-app Gemma boundary

Google AI Edge Gallery is also installed on the Fold7 and holds `gemma-4-E4B-it.litertlm` (3,659,530,240 bytes) in its app-specific external-storage tree. Research of the Gallery implementation and installed package found no supported exported model-serving API. Android scoped storage also prevents ONF or the document picker from silently browsing another application's `Android/data` directory.

ONF therefore detects Gallery only to explain the available choices. Production users must import an original/shared model with the system picker. The verified E4B benchmark used a development-only ADB copy into ONF's sandbox, with source and destination SHA-256 both equal to `0B2A8980CE155FD97673D8E820B4D29D9C7D99B8FA6806F425D969B145BD52E0`.

## Planned official SDK adapter

When the gated artifact and documentation are available, add `FoundryLocalEngine : LocalLlmEngine` with these responsibilities:

- connect through the documented companion SDK lifecycle;
- request a catalog model alias and allow Foundry to select the Fold7 variant;
- download with visible consent/progress and explicit model-license handling;
- expose model/backend/version status;
- stream bounded chat completions with cancellation;
- load `whisper-tiny` or the approved mobile speech alias for encrypted-segment transcription;
- unload models on memory pressure;
- map service absence/version mismatch to LiteRT fallback without losing session state.

No ONF domain, storage, RAG, skill, encryption, or Compose code should depend directly on the vendor SDK.

## Privacy gate

Current ONF LiteRT operation has no Android `INTERNET` permission and no telemetry SDK. Foundry Local companion preview has separate network and data terms. Its Play disclosure says it may collect app activity, app information/performance, and device identifiers, while reporting no third-party sharing.

Before enabling Foundry as the default runtime:

1. document exactly what preview telemetry is mandatory and optional;
2. expose the selected runtime and network boundary in the UI;
3. verify inference inputs and meeting audio are never transmitted;
4. provide an explicit fallback to the zero-network LiteRT path;
5. record model source, version, license, backend, and runtime in exported audit metadata;
6. rerun offline, airplane-mode, packet-capture, battery, thermal, and long-session tests.

## Current Fold7 fallback benchmark

The Apache-2.0 generic Gemma 4 E2B LiteRT-LM model is provisioned privately in ONF and has passed repeated real inference probes:

- SHA-256: `181938105E0EEFD105961417E8DA75903EACDA102C4FCE9CE90F50B97139A63C`;
- selected backend: CPU/XNNPACK fallback;
- cached load: 509–763 ms;
- deterministic readiness response: 1,629–1,841 ms;
- output: `ONF-FOLD7-READY.`

This keeps development unblocked while preserving a clean migration path to the official Foundry Android SDK.

The final two-model switch sequence also passed on the same Fold7: E2B loaded/generated in 523/2,755 ms, E4B in 13,581/6,391 ms, and returning to E2B in 1,502/2,609 ms. All three probes selected CPU/XNNPACK and returned their exact readiness tokens. A separate final E2B probe loaded/generated in 790/1,838 ms and returned `ONF-FOLD7-READY.` These are functional one-shot results, not sustained latency, quality, battery, or thermal claims.
