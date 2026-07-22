"""
Sample Data Generator
Creates realistic synthetic industrial documents and pre-loads them into the system.
Run: python scripts/generate_sample_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# ── Text content for sample PDFs (written as txt, parsed as PDF by pypdf alternative)
PUMP_P101_MANUAL = """
PUMP P-101 TECHNICAL MANUAL
Model: Centrifugal Pump CP-2400
Equipment ID: P-101
Location: Section A, Production Zone
Manufacturer: FlowMaster Industries

SPECIFICATIONS
Max Flow Rate: 450 m³/hr
Operating Pressure: 8-12 bar
Max Temperature: 180°C
Shaft Speed: 1450 RPM
Motor Power: 75 kW
Bearing Type: SKF 6312 Deep Groove

OPERATING LIMITS
Warning Temperature: 160°C
Critical Temperature: 175°C
Min Suction Pressure: 0.5 bar
Max Vibration: 4.5 mm/s RMS

MAINTENANCE SCHEDULE
Daily: Check vibration levels, temperature, pressure readings
Weekly: Lubricate bearings with Shell Tellus 46
Monthly: Inspect mechanical seal, check alignment
Quarterly: Full inspection including impeller clearance
Annual: Major overhaul — replace bearings, seals, impeller

TROUBLESHOOTING
Problem: High vibration
Causes: Bearing failure, misalignment, cavitation, unbalanced impeller
Action: Stop pump immediately, inspect bearings and alignment

Problem: Overheating
Causes: Low flow, high ambient temperature, bearing failure
Action: Check flow rates, inspect cooling system, replace bearings

Problem: Seal leakage
Causes: Worn seal faces, shaft runout, incorrect seal type
Action: Replace mechanical seal, check shaft alignment

SPARE PARTS LIST
Bearing Set: SKF 6312 (Qty: 2)
Mechanical Seal: Burgmann M7N-28 (Qty: 1)
Impeller: CP-2400-IMP (Qty: 1)
Shaft Sleeve: CP-2400-SS (Qty: 1)
"""

MAINTENANCE_RECORDS_CONTENT = """MAINTENANCE HISTORY REPORT - PLANT OPERATIONS
Generated: 2025-01-15
Plant: Tata Industrial Complex, Mumbai

EQUIPMENT: Pump P-101 (Centrifugal Pump)
Location: Section A

Record 1:
Date: 2024-03-20
Type: Corrective Maintenance
Operator: Ravi Kumar
Failure Mode: Bearing failure - excessive vibration detected at 6.2 mm/s
Action Taken: Replaced SKF 6312 bearing set, re-aligned shaft
Downtime: 8 hours
Risk Score: High

Record 2:
Date: 2024-05-15
Type: Preventive Maintenance
Operator: Suresh Sharma
Action Taken: Quarterly bearing lubrication, seal inspection
Seal Condition: OK
Risk Score: Low

Record 3:
Date: 2024-07-10
Type: Corrective Maintenance
Operator: Ravi Kumar
Failure Mode: Mechanical seal leakage - product contamination
Temperature at failure: 172°C (above 160°C warning limit)
Action Taken: Replaced Burgmann M7N-28 mechanical seal
Downtime: 12 hours
Root Cause: Overheating due to low flow condition
Risk Score: High

Record 4:
Date: 2024-09-05
Type: Emergency Maintenance
Operator: Amit Patel
Failure Mode: Complete bearing seizure - catastrophic failure
Vibration: 9.8 mm/s (far above 4.5 mm/s limit)
Temperature: 185°C (above critical 175°C limit)
Action Taken: Emergency shutdown, full bearing replacement, impeller inspection
Downtime: 24 hours
Cost: INR 85,000
Risk Score: Critical

Record 5:
Date: 2024-10-20
Type: Preventive Maintenance
Operator: Suresh Sharma
Action Taken: Post-failure inspection, alignment check, vibration baseline
Vibration: 2.1 mm/s (normal)
Risk Score: Low

EQUIPMENT: Compressor C-22
Location: Section B

Record 6:
Date: 2024-04-12
Type: Corrective Maintenance
Operator: Mohan Rao
Failure Mode: Valve failure - pressure drop across cylinder 3
Discharge Pressure: 45 bar (expected 52 bar)
Action Taken: Replaced suction and discharge valves on cylinder 3
Downtime: 16 hours
Risk Score: High

Record 7:
Date: 2024-08-18
Type: Preventive Maintenance
Operator: Mohan Rao
Action Taken: Semi-annual valve inspection, oil change, filter replacement
Status: Good condition
Risk Score: Low

EQUIPMENT: Boiler B-5
Location: Utility Block

Record 8:
Date: 2024-02-28
Type: Corrective Maintenance
Operator: Rajesh Singh
Failure Mode: Safety valve malfunction - failed to open at set pressure
Action Taken: Replaced safety valve SV-2000, pressure tested
Downtime: 6 hours
Risk Score: Critical - safety violation

Record 9:
Date: 2024-06-15
Type: Regulatory Inspection
Operator: Inspector Kumar (Factory Inspector)
Status: PASSED with observations
Observations: Water treatment dosing pump needs calibration
Next inspection due: December 2024
Risk Score: Medium
"""

INSPECTION_REPORT = """
QUARTERLY SAFETY INSPECTION REPORT
Report No: QSR-2024-Q3
Date: September 30, 2024
Inspector: Safety Officer Priya Mehta
Plant: Industrial Complex, Section A & B

EXECUTIVE SUMMARY
Overall Compliance Score: 78%
Critical Issues Found: 2
Major Issues Found: 5
Minor Issues Found: 8

SECTION 1: PERSONAL PROTECTIVE EQUIPMENT
Finding 1.1: PPE Compliance - FAIL
Location: Pump Area, Section A
Observation: 3 workers observed operating without safety helmets
Severity: CRITICAL
Action Required: Immediate - enforce PPE compliance, issue formal warning

Finding 1.2: Safety footwear - PASS
All personnel wearing appropriate steel-toed boots.

SECTION 2: EMERGENCY SYSTEMS
Finding 2.1: Emergency Exit B3 - FAIL
Location: Section B, East Wing
Observation: Emergency exit partially blocked by stored materials (valve inventory)
Severity: CRITICAL
Action Required: Clear emergency exit within 24 hours

Finding 2.2: Fire extinguishers - PASS
All 24 fire extinguishers inspected, 22 within service date.
2 units in Storage Room 4 expired on August 15 - replace immediately.

Finding 2.3: Emergency shutdown system - PASS
ESD system tested successfully. Response time: 2.3 seconds.

SECTION 3: EQUIPMENT SAFETY
Finding 3.1: Pump P-101 Guarding - PASS
All rotating parts properly guarded.

Finding 3.2: Pressure Vessel PV-7 - WARNING
Last inspection certificate expired. Renewal required within 30 days.

Finding 3.3: Lockout/Tagout Procedures - PARTIAL
LOTO station found incomplete at Compressor C-22.
Missing: 3 lockout hasps, tag documentation not current.

SECTION 4: HOUSEKEEPING
Finding 4.1: Oil spill in Pump P-101 area - Minor
Small oil puddle beneath pump - likely from recent seal replacement.
Action: Clean up and monitor for recurrence.

RECOMMENDATIONS
1. Immediate: Clear emergency exit B3 and enforce PPE compliance
2. 30 days: Renew PV-7 pressure vessel inspection certificate
3. 30 days: Complete LOTO station at C-22
4. 7 days: Replace expired fire extinguishers in Storage Room 4
5. Ongoing: Increase safety training frequency for Section A personnel
"""

SAFETY_SOP = """
SAFETY STANDARD OPERATING PROCEDURES
Document: SOP-HSE-001
Version: 3.2
Approved by: VP Operations
Effective Date: January 1, 2024

1. PERSONAL PROTECTIVE EQUIPMENT (PPE)
1.1 Mandatory PPE in all production areas:
    - Safety helmet (EN 397 certified)
    - Safety footwear (EN ISO 20345:2011 S3)
    - Safety glasses (EN 166)
    - High-visibility vest
    
1.2 Additional PPE for specific tasks:
    - Chemical resistant gloves for acid handling
    - Face shield for overhead work
    - Hearing protection where noise > 85 dBA
    - Respiratory protection for dust/chemical exposure

2. EMERGENCY PROCEDURES
2.1 Emergency exits must be kept clear AT ALL TIMES
2.2 Minimum 1 meter clearance on all sides of emergency exits
2.3 Emergency evacuation assembly point: Car Park B
2.4 Emergency contact numbers must be posted at every workstation

3. EQUIPMENT SAFETY
3.1 Lockout/Tagout (LOTO):
    - All energy sources must be isolated before maintenance
    - LOTO procedure must be documented for each equipment
    - Personal lock must be used by each worker
    
3.2 Pressure Vessels:
    - Valid inspection certificate required at all times
    - Safety valve must be tested annually
    - Operating log must be maintained

3.3 Rotating Equipment:
    - Guards must be in place during operation
    - Vibration monitoring mandatory for critical pumps
    - Bearing temperature monitored monthly minimum

4. INCIDENT REPORTING
4.1 All incidents must be reported within 1 hour
4.2 Near-misses must be documented on Form HSE-007
4.3 Fatal/serious injuries: Notify Factory Inspector within 12 hours (Factory Act requirement)

5. COMPLIANCE REQUIREMENTS (FACTORY ACT 1948)
5.1 Annual safety audit mandatory
5.2 Workers must receive safety training every 6 months
5.3 First aid facilities must be maintained per Schedule 5
5.4 Noise levels must not exceed 90 dBA (8-hour TWA)
5.5 Pressure vessel certification per IBR Regulations
"""

BOILER_INCIDENT = """
INCIDENT INVESTIGATION REPORT
Report No: IIR-2024-012
Date of Incident: March 15, 2024
Location: Boiler House, Boiler B-5
Severity: HIGH - Near Miss

INCIDENT DESCRIPTION
At approximately 14:35 hrs, the duty operator Rajesh Singh noticed unusual noise 
from Boiler B-5 followed by steam discharge from an unexpected location.
Investigation revealed that safety valve SV-B5-001 failed to lift at the design 
set pressure of 12 bar. Steam pressure continued to rise to 13.8 bar before 
operator manually reduced fuel input.

IMMEDIATE ACTIONS TAKEN
1. Manual reduction of fuel input
2. Boiler taken offline
3. Safety officer and plant manager notified
4. Area evacuated as precaution

ROOT CAUSE ANALYSIS
Primary Cause: Safety valve SV-B5-001 seat corrosion due to water quality issues
Contributing Factor 1: Water treatment system malfunctioning since February 2024
Contributing Factor 2: Last safety valve test was 18 months ago (overdue by 6 months)
Contributing Factor 3: Water quality monitoring logs not reviewed for 2 months

CORRECTIVE ACTIONS
1. Replaced safety valve SV-B5-001 with new Spirax Sarco SV27 (Completed: March 16)
2. Water treatment system repaired and dosing corrected (Completed: March 18)
3. All boiler safety valves inspected (Completed: March 20)
4. Safety valve testing frequency changed from annual to 6-monthly
5. Water quality monitoring made daily mandatory task

LESSONS LEARNED
1. Preventive maintenance schedules must be strictly followed
2. Water quality directly impacts boiler safety valve reliability
3. Near-miss reporting culture needs improvement - incident almost not reported
4. Cross-checking between maintenance schedule and actual completion is critical

Equipment affected: Boiler B-5 (B-5)
Operator involved: Rajesh Singh
Witness: Operator Sunil Verma
"""


async def generate_sample_data():
    """Create all sample documents and seed the database"""
    import asyncio

    print("🏭 Generating Industrial Knowledge Intelligence Sample Data...")

    # Create directories
    os.makedirs("./uploads", exist_ok=True)
    os.makedirs("./reports", exist_ok=True)

    # Write text files (simulating documents)
    sample_docs = [
        ("Pump_P101_Manual.txt", PUMP_P101_MANUAL),
        ("Maintenance_History_2024.txt", MAINTENANCE_RECORDS_CONTENT),
        ("Inspection_Report_Q3_2024.txt", INSPECTION_REPORT),
        ("Safety_SOP_Guidelines.txt", SAFETY_SOP),
        ("Boiler_B5_Incident_Report.txt", BOILER_INCIDENT),
    ]

    doc_paths = []
    for filename, content in sample_docs:
        path = f"./uploads/{filename}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        doc_paths.append((path, filename))
        print(f"  ✅ Created: {filename}")

    # Initialize DB
    from core.database import init_db, AsyncSessionLocal, Document, MaintenanceRecord
    await init_db()

    # Seed maintenance records directly
    maintenance_records = [
        # Pump P-101 records
        dict(document_id=2, equipment_id="P-101", equipment_name="Pump P-101",
             maintenance_type="corrective", description="Replaced SKF 6312 bearing set, re-aligned shaft",
             operator="Ravi Kumar", location="Section A", failure_mode="Bearing failure - excessive vibration",
             risk_score="High", status="completed",
             maintenance_date=datetime(2024, 3, 20)),
        dict(document_id=2, equipment_id="P-101", equipment_name="Pump P-101",
             maintenance_type="preventive", description="Quarterly bearing lubrication, seal inspection",
             operator="Suresh Sharma", location="Section A", failure_mode=None,
             risk_score="Low", status="completed",
             maintenance_date=datetime(2024, 5, 15)),
        dict(document_id=2, equipment_id="P-101", equipment_name="Pump P-101",
             maintenance_type="corrective", description="Replaced mechanical seal - overheating at 172°C",
             operator="Ravi Kumar", location="Section A", failure_mode="Mechanical seal leakage",
             risk_score="High", status="completed",
             maintenance_date=datetime(2024, 7, 10)),
        dict(document_id=2, equipment_id="P-101", equipment_name="Pump P-101",
             maintenance_type="emergency", description="Emergency shutdown, full bearing replacement",
             operator="Amit Patel", location="Section A", failure_mode="Complete bearing seizure",
             risk_score="Critical", status="completed", cost=85000,
             maintenance_date=datetime(2024, 9, 5)),
        dict(document_id=2, equipment_id="P-101", equipment_name="Pump P-101",
             maintenance_type="preventive", description="Post-failure inspection, alignment check",
             operator="Suresh Sharma", location="Section A", failure_mode=None,
             risk_score="Low", status="completed",
             maintenance_date=datetime(2024, 10, 20)),
        # Compressor C-22
        dict(document_id=2, equipment_id="C-22", equipment_name="Compressor C-22",
             maintenance_type="corrective", description="Replaced suction and discharge valves on cylinder 3",
             operator="Mohan Rao", location="Section B", failure_mode="Valve failure - pressure drop",
             risk_score="High", status="completed",
             maintenance_date=datetime(2024, 4, 12)),
        dict(document_id=2, equipment_id="C-22", equipment_name="Compressor C-22",
             maintenance_type="preventive", description="Semi-annual valve inspection, oil change",
             operator="Mohan Rao", location="Section B", failure_mode=None,
             risk_score="Low", status="completed",
             maintenance_date=datetime(2024, 8, 18)),
        # Boiler B-5
        dict(document_id=5, equipment_id="B-5", equipment_name="Boiler B-5",
             maintenance_type="corrective", description="Replaced safety valve SV-B5-001",
             operator="Rajesh Singh", location="Utility Block", failure_mode="Safety valve malfunction",
             risk_score="Critical", status="completed",
             maintenance_date=datetime(2024, 3, 16)),
        dict(document_id=3, equipment_id="B-5", equipment_name="Boiler B-5",
             maintenance_type="preventive", description="Regulatory inspection - PASSED with observations",
             operator="Inspector Kumar", location="Utility Block", failure_mode=None,
             risk_score="Medium", status="completed",
             maintenance_date=datetime(2024, 6, 15)),
    ]

    # Insert maintenance records
    async with AsyncSessionLocal() as db:
        # Insert documents
        for i, (path, name) in enumerate(doc_paths):
            file_size = os.path.getsize(path)
            doc = Document(
                filename=os.path.basename(path),
                original_name=name,
                file_type="txt",
                file_size=file_size,
                status="ready",
                page_count=1,
                chunk_count=5,
                summary=f"Sample industrial document: {name}",
            )
            db.add(doc)
        await db.flush()

        for record in maintenance_records:
            mr = MaintenanceRecord(**record)
            db.add(mr)
        await db.commit()
        print(f"  ✅ Seeded {len(maintenance_records)} maintenance records")

    # Initialize vector store and embed sample docs
    from core.vectorstore import init_vectorstore, add_documents
    from core.llm import get_embeddings
    init_vectorstore()

    print("  📦 Generating embeddings for sample documents...")
    from agents.ingestion_agent import chunk_text

    try:
        embed_model = get_embeddings()
        all_chunks, all_ids, all_metas = [], [], []
        for doc_id, (path, name) in enumerate(doc_paths, start=1):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            chunks = chunk_text(text)
            for j, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"sample_doc_{doc_id}_chunk_{j}")
                all_metas.append({
                    "document_id": str(doc_id),
                    "document_name": name,
                    "page": "1",
                    "chunk_index": str(j),
                    "file_type": "txt",
                })

        if all_chunks:
            add_documents(texts=all_chunks, ids=all_ids, metadatas=all_metas)
            print(f"  ✅ Embedded {len(all_chunks)} chunks into ChromaDB")
    except Exception as e:
        print(f"  ⚠️  Embedding skipped (need valid GEMINI_API_KEY): {e}")

    # Build knowledge graph from sample entities
    from core.knowledge_graph import knowledge_graph
    knowledge_graph.load()

    # Add sample entities manually
    _seed_knowledge_graph(knowledge_graph)
    knowledge_graph.save()
    print("  ✅ Knowledge graph seeded")
    print("\n🎉 Sample data generation complete!")
    print("   Documents: 5")
    print("   Maintenance Records: 9")
    print("   Equipment: P-101, C-22, B-5")
    print("\n▶️  Now run: uvicorn main:app --reload")


def _seed_knowledge_graph(kg):
    """Pre-seed knowledge graph with sample entities"""
    # Equipment nodes
    kg.add_entity("equipment_p_101", "equipment", "Pump P-101",
                  {"equipment_id": "P-101", "equipment_type": "centrifugal pump", "name": "Pump P-101"})
    kg.add_entity("equipment_c_22", "equipment", "Compressor C-22",
                  {"equipment_id": "C-22", "equipment_type": "reciprocating compressor", "name": "Compressor C-22"})
    kg.add_entity("equipment_b_5", "equipment", "Boiler B-5",
                  {"equipment_id": "B-5", "equipment_type": "steam boiler", "name": "Boiler B-5"})

    # Locations
    kg.add_entity("location_section_a", "location", "Section A", {"name": "Section A", "zone": "Production"})
    kg.add_entity("location_section_b", "location", "Section B", {"name": "Section B", "zone": "Compression"})
    kg.add_entity("location_utility", "location", "Utility Block", {"name": "Utility Block", "zone": "Utilities"})

    # Operators
    kg.add_entity("operator_ravi_kumar", "operator", "Ravi Kumar", {"name": "Ravi Kumar", "role": "maintenance engineer"})
    kg.add_entity("operator_mohan_rao", "operator", "Mohan Rao", {"name": "Mohan Rao", "role": "maintenance engineer"})
    kg.add_entity("operator_rajesh_singh", "operator", "Rajesh Singh", {"name": "Rajesh Singh", "role": "operations engineer"})
    kg.add_entity("operator_suresh_sharma", "operator", "Suresh Sharma", {"name": "Suresh Sharma", "role": "maintenance supervisor"})

    # Failure events
    kg.add_entity("failure_p101_bearing_mar24", "failure_event", "Bearing Failure Mar-2024",
                  {"failure_mode": "Bearing failure - excessive vibration", "date": "2024-03-20", "equipment": "P-101"})
    kg.add_entity("failure_p101_seal_jul24", "failure_event", "Seal Leakage Jul-2024",
                  {"failure_mode": "Mechanical seal leakage", "date": "2024-07-10", "equipment": "P-101"})
    kg.add_entity("failure_p101_seizure_sep24", "failure_event", "Bearing Seizure Sep-2024",
                  {"failure_mode": "Complete bearing seizure - catastrophic", "date": "2024-09-05", "equipment": "P-101"})
    kg.add_entity("failure_c22_valve_apr24", "failure_event", "Valve Failure Apr-2024",
                  {"failure_mode": "Valve failure - pressure drop", "date": "2024-04-12", "equipment": "C-22"})
    kg.add_entity("failure_b5_safety_valve_mar24", "failure_event", "Safety Valve Failure Mar-2024",
                  {"failure_mode": "Safety valve malfunction - near miss", "date": "2024-03-15", "equipment": "B-5"})

    # Relationships
    kg.add_relationship("equipment_p_101", "location_section_a", "LOCATED_IN")
    kg.add_relationship("equipment_c_22", "location_section_b", "LOCATED_IN")
    kg.add_relationship("equipment_b_5", "location_utility", "LOCATED_IN")

    kg.add_relationship("operator_ravi_kumar", "equipment_p_101", "MAINTAINS")
    kg.add_relationship("operator_mohan_rao", "equipment_c_22", "MAINTAINS")
    kg.add_relationship("operator_rajesh_singh", "equipment_b_5", "MAINTAINS")

    kg.add_relationship("equipment_p_101", "failure_p101_bearing_mar24", "HAD_FAILURE")
    kg.add_relationship("equipment_p_101", "failure_p101_seal_jul24", "HAD_FAILURE")
    kg.add_relationship("equipment_p_101", "failure_p101_seizure_sep24", "HAD_FAILURE")
    kg.add_relationship("equipment_c_22", "failure_c22_valve_apr24", "HAD_FAILURE")
    kg.add_relationship("equipment_b_5", "failure_b5_safety_valve_mar24", "HAD_FAILURE")


if __name__ == "__main__":
    asyncio.run(generate_sample_data())
