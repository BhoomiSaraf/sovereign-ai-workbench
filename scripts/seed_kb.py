from datetime import datetime, timezone
from pathlib import Path
import os
import sys


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


KNOWLEDGE_DIR = ROOT / "data" / "knowledge_base"

DEMO_DOCUMENTS = {
    "MRPL_Maintenance_SOP.md": """# MRPL Mechanical Maintenance Standard Operating Procedure

Document Number: MRPL-MNT-SOP-204
Revision: 6
Effective Date: 2026-04-01
Plant: Mangalore Refinery and Petrochemicals Limited
Classification: Internal / Restricted

## Purpose and Scope

This SOP governs planned and opportunistic mechanical maintenance of rotating equipment in crude, hydrocracker, and utilities areas. It applies to centrifugal pumps, steam turbines, and associated piping within the battery limits of process units. Field execution shall remain consistent with the approved permit-to-work system, isolation standards, and the current inspection strategy.

The procedure does not authorize deviation from statutory boiler, pressure-vessel, or electrical safety rules. Where this SOP conflicts with a statutory requirement, the statutory requirement prevails and the conflict shall be recorded in the maintenance work pack.

## Pump Visual Inspection

Visual inspection of centrifugal pumps shall be completed at the start of every shift by the area operator and again by the mechanical technician before issuing a fit-for-service recommendation.

The inspector shall record:
- Coupling guard integrity and fastener completeness
- Seal pot level, colour, and visible leakage at the gland or seal face
- Bearing housing temperature by touchpoint indicator or calibrated IR gun
- Abnormal noise, knocking, or rubbing at the coupling and pump casing
- Foundation bolt tightness, baseplate grout cracks, and pipe strain evidence
- Suction and discharge isolation valve positions versus the P&ID
- Presence of oil, hydrocarbon, or utility water staining on the skid

Photographs shall be stored in the local inspection folder. Visual inspection is evidence of observed condition only. It is not by itself a declaration that the pump is healthy, failed, or available for operation.

### Inspection Sequence

1. Confirm the equipment tag against the work order and P&ID.
2. Verify that the area is covered by a valid permit and gas test where required.
3. Walk the suction line, pump casing, seal system, and discharge line in that order.
4. Record each observation as seen, uncertain, or not visible.
5. Do not infer internal wear from external appearance unless a supporting measurement exists.

## Criteria for Failure

A pump shall be declared unfit for continued operation, and a work request raised as urgent, when any of the following criteria are met:

- Visible hydrocarbon spray, dripping, or pooling at the mechanical seal that cannot be attributed to residual wash water
- Bearing housing temperature exceeding 85 °C for hydrocarbon services or 90 °C for cooling-water services
- Peak vibration exceeding 7.1 mm/s RMS on the bearing housing in any plane
- Coupling guard missing, displaced, or with loose fasteners
- Loss of seal flush or barrier fluid with no immediate restoration path
- Suction strainer differential pressure above the vendor limit for more than two consecutive rounds
- Foundation movement, cracked grout with increasing gap, or loose hold-down bolts

Uncertain staining, historical discoloration, or a single noisy observation without corroborating temperature or vibration data shall be logged as a verification item, not as a confirmed failure.

## Isolation and Handover

Before intrusive maintenance, the equipment owner shall isolate energy sources using the plant LOTOTO procedure. Blinds shall be installed at the suction and discharge flanges for hydrocarbon pumps. The mechanical supervisor shall not accept the equipment until the isolation certificate, gas-test record, and drain/vent confirmation are attached to the work pack.

## Post-Maintenance Checks

After reassembly, the technician shall confirm rotation direction, coupling alignment within 0.05 mm offset, lubricant grade and level, and seal flush restoration. A supervised run-in of thirty minutes is required before returning the pump to normal service. Run-in observations shall be written into the same work order used for the original defect.

## Records and Retention

Inspection sheets, vibration snapshots, and approval notes shall be retained in the local maintenance archive for a minimum of seven years. Records are organizational evidence and must not be altered after approval.
""",
    "Delegation_of_Power_2026.md": """# Delegation of Power 2026

Document Number: CORP-DOP-2026
Owner: Finance and Contracts
Applicability: Refinery, petrochemical, and pipelines business units
Classification: Internal

## Purpose

This schedule defines financial approval limits for maintenance, inspection, emergency purchase, and contract variation. It replaces the 2024 schedule with effect from 01 January 2026. Approvals outside these limits are invalid even if a local manager has signed them.

## Maintenance Department Limits

Routine mechanical and electrical maintenance expenditure may be approved as follows:

- Shift Engineer / Area Engineer: up to INR 50,000 per work order for consumables and minor repairs
- Mechanical Maintenance Manager: up to INR 5,00,000 per work order, including shop repairs and vendor call-outs
- General Manager (Maintenance): up to INR 25,00,000 per work order or campaign
- Executive Director (Refinery): above INR 25,00,000, subject to finance concurrence

Split purchase orders issued to stay under a limit are prohibited. Repeat work on the same tag within thirty days shall be aggregated when testing against these limits.

## Inspection and Reliability Limits

Inspection, NDT, and specialist reliability contracts:

- Inspection Engineer: up to INR 1,00,000 for local NDT call-out
- Head of Inspection: up to INR 10,00,000 for planned thickness survey or turnaround NDT packages
- General Manager (Technical): up to INR 40,00,000 for residual-life studies and third-party fitness-for-service

Emergency inspection after a leak, fire, or overpressure event may be authorized by the Shift Superintendent up to INR 2,00,000, with ratification by Head of Inspection within two working days.

## Operations and Safety Limits

- Operations Manager: up to INR 2,00,000 for temporary hose, clamp, or bypass arrangements required to keep a unit safe
- Chief Manager (HSE): up to INR 7,50,000 for emergency response equipment, spill control, and third-party industrial hygiene
- Occupier / Site Head: unlimited for imminent danger to life, with a written incident note within twenty-four hours

Temporary clamps on hydrocarbon lines remain a safety control, not a permanent repair. Financial approval of a clamp does not constitute engineering acceptance of continued operation beyond the stated validity period.

## Contracts and Variations

Contract variations on running maintenance AMCs:

- Up to 10 percent of the original value or INR 15,00,000, whichever is lower: General Manager of the owning department
- Above that threshold: Contracts Committee with Finance representation

## Documentation Required With Every Approval

Every approval note shall cite the SOP or inspection finding that justifies the spend, the tag number, the requested amount, the approving authority, and residual uncertainty. Missing citation of source documents is grounds for finance rejection.
""",
    "Safety_Protocol_Hazardous_Leaks.md": """# Safety Protocol for Hazardous Leaks

Document Number: HSE-LEAK-PROT-11
Revision: 4
Site: Onshore refining and petrochemical complex
Classification: Safety Critical

## Immediate Actions

On discovery of a suspected hydrocarbon, hydrogen, sour-gas, or corrosive-chemical leak, the discoverer shall:

1. Stop work in the immediate area and warn nearby personnel without creating a crowd.
2. Move upwind or cross-wind to a safe muster reference, not into a confined collection point.
3. Raise the area radio alarm and state the tag, unit, and observed evidence only.
4. Do not approach spray, vapour clouds, or pools to "confirm" the leak if the first observation is already unambiguous.

The Shift Superintendent owns the scene until the incident is stood down.

## Classification of Leak Severity

- Level 1: staining, dampness, or historical residue with no active drip or spray
- Level 2: active drip or mist with no ignition source and gas readings below 10 percent LEL outside 1 metre
- Level 3: spray, vapour cloud, gas at or above 10 percent LEL, H2S above occupational limits, or any leak that cannot be isolated from the field

Level 1 is a verification condition. It shall not be described as a confirmed hazardous leak in reports.

## Isolation and Emergency Shutdown

For Level 2 and Level 3 events, isolation shall follow the unit ESD hierarchy. Manual isolation of the nearest valves is permitted only when:

- The person is wearing the correct PPE for the service
- Approach does not require crossing the vapour envelope
- A backup observer is in radio contact
- The valve is identified on the P&ID and is not a control valve relied upon for unit stability without board concurrence

If those conditions are not met, isolation shall be performed from the control room or a remote station.

## PPE and Exclusion Zones

Minimum PPE for Level 2 hydrocarbon response is fire-retardant clothing, face shield, chemical gloves, and a personal H2S monitor in sour services. Level 3 requires BA sets for entry into the exclusion zone. The default exclusion radius is 15 metres for Level 2 and 30 metres for Level 3, expanded if wind carries vapour toward furnaces, substations, or occupied buildings.

## Communication and Medical

Control room shall notify fire and safety, occupational health, and the on-call maintenance manager. Anyone exposed to sour gas, benzene, or corrosive splash shall report to the medical centre even if they feel well. Clothing that is soaked with hydrocarbon shall be removed and bagged; it is not to be worn into the control room.

## Restart Criteria

The unit or equipment shall not be restarted until:

- The leak path is isolated or mechanically secured
- Gas readings are below 1 percent LEL in the former exclusion zone
- A written cause hypothesis exists, even if incomplete
- Inspection has stated whether remaining thickness or clamp integrity is adequate
- Operations, Maintenance, and HSE have jointly signed a restart note

Absence of visible spray after isolation is not sufficient restart evidence by itself.
""",
    "Past_Inspection_Report_Valve_A4.md": """# Past Inspection Report — Valve A4

Report Number: INSP-VALVE-A4-2026-08
Equipment Tag: P-204-A4 (discharge isolation valve, centrifugal pump P-204 A)
Service: Hydrocarbon distillate, design pressure 40 barg, operating 18 to 22 barg
Inspection Date: 12 August 2026
Inspector: K. Rao, API 570 authorized
Classification: Internal inspection record

## Equipment Identification

Valve A4 is a 6-inch class 300 gate valve on the discharge of pump P-204 A. The upstream flange connects to the pump discharge check valve. The downstream flange connects to the unit discharge header. The valve is normally open during pump operation and is a designated isolation point in the LOTOTO scheme.

Nameplate data recorded on site matched the master equipment list: body ASTM A216 WCB, trim 13Cr, graphite packing, and flexible graphite spiral-wound gaskets.

## Findings

External visual inspection found brown hydrocarbon staining on the downstream flange at the 6 o'clock position. No active drip was observed during the 25-minute hold. Packing gland fasteners were present and equally engaged. The handwheel was operable. No steam or process tracing damage was noted on the adjacent pipe.

Ultrasonic thickness on the adjacent 6-inch spool showed a minimum of 7.2 mm against a nominal 7.11 mm specified wall plus corrosion allowance of 3.0 mm on the original datasheet. Remaining life calculation was not performed in this visit because the reading is above retirement thickness. The staining therefore remains an unresolved leak-path verification item, not proof of through-wall failure.

A faint solvent odour was noted near the packing; portable LEL remained 0 percent at 10 cm from the gland.

## Previous History

The 2025 turnaround replaced the spiral-wound gasket on the downstream flange. Packing was adjusted in March 2026 after operators reported a smell during night shift. No clamp has been installed on this tag. Vibration of pump P-204 A was last recorded at 3.4 mm/s RMS, which is below the failure threshold in the mechanical SOP.

## Recommendations

1. Re-inspect Valve A4 packing and downstream flange during the next two operating shifts and photograph the 6 o'clock staining under consistent lighting.
2. If an active drip appears, isolate per the hazardous leak protocol and raise an urgent work order. Do not describe historical staining as a confirmed leak in the approval note.
3. Include Valve A4 in the next planned packing replacement window. Estimated material and labour is INR 85,000, which falls within the Mechanical Maintenance Manager's delegation.
4. Do not declare the pump or valve unfit for service solely on the basis of this report.

## Uncertainties

Operational status of P-204 A cannot be determined from this inspection record alone. The report does not establish whether the pump is currently running. Fitness for service of the valve body is supported by thickness readings but packing leak-tightness requires live verification.

## Attachments

Local file references: A4_flange_photo_01.jpg, A4_UT_log_20260812.csv, P204_vibration_20260810.txt. These attachments are stored on the plant inspection share and were not transferred outside the site.
""",
}


def write_demo_documents(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for filename, content in DEMO_DOCUMENTS.items():
        path = output_dir / filename
        path.write_text(content.strip() + "\n", encoding="utf-8")
        written.append(path)
        print(f"Wrote {path.relative_to(ROOT)}")

    return written


def ingest_documents(paths: list[Path]) -> dict[str, object]:
    from app.rag.ingest import KnowledgeIngester
    from app.rag.store import ChromaStore

    ingester = KnowledgeIngester()
    summary: dict[str, object] = {
        "files": {},
        "total_chunks": 0,
        "errors": [],
        "date_ingested": datetime.now(timezone.utc).date().isoformat(),
    }

    for path in paths:
        print(f"Ingesting {path.name} ...")
        result = ingester.ingest_file(str(path))

        if result.get("status") != "ingested":
            error = result.get("error", "unknown error")
            summary["errors"].append(
                {"file": path.name, "error": error}
            )
            print(f"  ERROR: {error}")
            continue

        chunk_count = int(result.get("chunks") or 0)
        summary["files"][path.name] = chunk_count
        summary["total_chunks"] = int(summary["total_chunks"]) + chunk_count
        print(f"  {chunk_count} chunks")

    summary["store_count"] = ChromaStore().count()
    return summary


def main() -> int:
    print("Seeding local organizational knowledge base...")
    print(f"Target directory: {KNOWLEDGE_DIR}")

    try:
        paths = write_demo_documents(KNOWLEDGE_DIR)
        summary = ingest_documents(paths)
    except Exception as exc:
        print(f"Seed failed: {exc}")
        return 1

    print("\nSummary")
    for filename, chunks in summary["files"].items():
        print(f"  {filename}: {chunks} chunks")

    print(f"  Total ingested this run: {summary['total_chunks']}")
    print(f"  ChromaDB collection count: {summary['store_count']}")

    if summary["errors"]:
        print("Completed with errors.")
        return 1

    print("Seed complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
