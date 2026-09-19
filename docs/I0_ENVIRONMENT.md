# I0 diagnostic environment preparation

Updated: 2026-09-19. Current status: **MANUAL OUTCOME UNKNOWN; I0 NOT ACCEPTED**.

## Current readback — 2026-09-19

Read-only configuration inspection at 11:38 UTC found the diagnostic guest
powered off, one NAT adapter enabled, the other seven adapters disabled,
clipboard and drag/drop disabled, and no reported shared folders or forwarding.
The only listed snapshot preserves the earlier black-screen fault; no accepted
candidate software baseline was observed.

No owner result has established black-screen recovery, Windows first-boot
completion, guest Mnova installation/activation, offline operation or rollback.
Those outcomes remain **unknown**. Poweroff does not prove installation success
or continued installation. NAT remains a setup exception, not accepted offline
isolation. The retained manual instructions describe a historical handoff; this
readback does not resume them.

This documentation update performs no VM or native action. P0 is not installed,
P1 has not been admitted, and scientific writes, target close and failed-request
replay remain disabled. Governance-approved Product Max takeover does not
change I0 acceptance.

## Historical preparation — 2026-09-16

Recorded status at that checkpoint: **OWNER LICENCE STEP COMPLETE / WINDOWS
INSTALLING; GUEST INSTALLATION INCOMPLETE; I0 NOT ACCEPTED**.
The preparation observations below retain their 2026-09-16 scope.

Following [P0](P0_EXECUTION.md), the owner authorized the next environment phase
and confirmed there is no dedicated VM or spare computer to reuse. The selected
candidate is a local VirtualBox Windows guest. This is a development diagnostic
environment, not an ordinary-user product installation requirement.

## Prepared — historical 2026-09-16 observations

- Fresh host inventory: Windows 11 Home China build 26200, x64. Existing
  hypervisor/VMP retained. WHP was enabled through DISM; the owner subsequently
  restarted the host. Fresh last-boot time is 2026-09-16 17:36:23.5 UTC; VMP and
  WHP both read back enabled.
- Official VirtualBox 7.2.18-175117 installer downloaded privately. Its 178,021,472
  bytes match Oracle's published SHA-256; Oracle signature valid.
- Official Mnova 17.0.1-41952 per-user MSI downloaded for the future guest only.
  Its 474,656,768 bytes have a valid Mestrelab signature. Local SHA-256 recorded;
  no independent vendor checksum observed. The Mnova installer was not executed.
- Owner completed Oracle installation. Installed VBoxManage version/signature
  readback passed at 7.2.18r175117; no extension packs, VBoxSup driver running.
- Created a blank VM: 4 vCPU, 4 GiB RAM, 80 GiB dynamic normal-mode
  disk, EFI/Secure Boot and TPM 2.0. Read back 23 settings and no shared folders.
  All network adapters, clipboard, drag/drop, USB, audio and remote display are
  disabled. It has now booted to the EFI Boot Manager using the NEM/WHP backend;
  the log records WHv partition creation. No installed guest OS is accepted.
- Owner-provided Windows 11 Enterprise Evaluation 25H2 x64 zh-CN ISO verified:
  7,371,034,624 bytes, SHA-256
  `7b4ac87391b659f7724229682b642256289a1c00504056249f0f12029157d3d2`,
  matching Microsoft's published table. It is attached to the DVD drive.
- The owner completed the short DVD boot-key prompt. Windows Setup was observed
  and advanced through language, keyboard and new-installation selection to
  the licence terms page. The owner then reported acceptance; disk selection and
  the installation-progress screen were independently observed. Only the new
  80 GiB VDI is attached as a disk. Default unattended media were not generated.
- OS-only rollback drill and private evidence handoff specified, not executed.

## Remaining gates — reviewed 2026-09-19

| Gate | State |
| --- | --- |
| Host restart after WHP enablement | HISTORICAL VERIFIED: VMP/WHP enabled after the 2026-09-16 owner restart; no new host restart performed |
| Guest Windows evaluation media/setup | HISTORICAL media integrity and owner terms/progress observation; current first-boot/account/activation outcome UNKNOWN |
| VM configuration and backend | HISTORICAL NEM/WHP runtime; CURRENT powered off with NAT setup exception and only a fault snapshot; isolation and rollback NOT ACCEPTED |
| Guest Mnova permission, installation, activation and static build | UNKNOWN: no owner manual result or independently accepted guest build/permission record |
| Automation/server permission for the proposed external executor | UNCONFIRMED; separate from ordinary guest activation |
| I0 acceptance and P1 runtime identity/O1 bootstrap | BLOCKED |

Host resources and disabled networking/integration were checked at the
2026-09-16 preparation checkpoint. The current readback instead has a NAT setup
exception. End and verify that exception before accepting diagnostic isolation;
record setup/activation exceptions separately. Use explicit read-only
inputs and a dedicated evidence export stage. No user profile, scientific files,
host licence directory or supervisor authority journal is shared with the guest.

Take powered-off baselines and prove rollback with OS-only markers. After the
final software, permission/activation steps and configuration are complete,
create the final diagnostic baseline and verify its restored configuration and
static build hashes before using it for P1. An OS-only drill would not by itself
accept this final software baseline. Supervisor
intent, consumed attempts, unknown-outcome quarantine and sealed evidence remain
outside snapshots and outside guest write access. A restore creates a new
environment incarnation; it does not clear history or authorize replay.

The independent OS/configuration boundary must be accepted before P1. The first P1
bootstrap then verifies actual guest process creation identity, loaded build and
execution context; this avoids requiring a native probe to pass I0 first.
P0's `portable_fake` admission is not a native execution route. Scientific writes,
target close, public native dispatch and failed-case replay remain disabled.

The following scope statement belongs to the 2026-09-16 preparation:
VirtualBox installation, post-reboot WHP/VMP checks, official ISO integrity and
bounded VM startup and navigation through owner licence acceptance to disk
installation are recorded. Guest completion remains unaccepted. No Mnova native
probe ran, no product source changed and no
installed-plugin update occurred. Existing portable, cloud and installed-host
product receipts retain their own recorded revision and scope.

## Historical preparation scope and references

- [Oracle minimal installation](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/installation.html)
- [Oracle WHP coexistence](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/AdvancedTopics.html)
- [Pinned Oracle package checksums](https://download.virtualbox.org/virtualbox/7.2.18/SHA256SUMS)
- [Microsoft Windows evaluation](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-11-enterprise)
- [Microsoft ISO verification table](https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/bade/documents/products-and-services/en-us/owned-and-operated/Verify-Download-Win11-Enterprise.pdf)
- [Mestrelab downloads](https://mestrelab.com/download)
- [Mestrelab EULA, sections 9.2 and 15.5](https://mestrelab.com/end-user-software-license-agreements)
