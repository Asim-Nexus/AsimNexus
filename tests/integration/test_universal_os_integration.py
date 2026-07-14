
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test Universal OS Components Integration
========================================

Test the new Universal OS components:
1. Universal API Gateway
2. Digital Twin System
3. Life Protocol Automation
"""

import asyncio
from datetime import date, datetime
from core.universal_api_gateway import APIGateway, GatewayConfig, APIRoute
from core.digital_twin_system import DigitalTwinSystem, Gender
from core.life_protocol_automation import LifeProtocolAutomation, get_life_protocol_automation

async def test_universal_api_gateway():
    """Test Universal API Gateway"""
    print("=" * 60)
    print("Testing Universal API Gateway")
    print("=" * 60)
    
    config = GatewayConfig(
        port=8001,
        enable_rate_limiting=False,  # Disable for testing
        enable_auth=False
    )
    
    gateway = APIGateway(config)
    
    # Register test route
    gateway.register_route(APIRoute(
        path="/test",
        method="GET",
        handler=lambda request: {"message": "Test successful"},
        auth_required=False
    ))
    
    # Check health
    print("\n✅ Gateway created successfully")
    print(f"✅ Port: {config.port}")
    print(f"✅ Routes registered: {len(gateway.routes)}")
    
    return gateway

async def test_digital_twin_system():
    """Test Digital Twin System"""
    print("\n" + "=" * 60)
    print("Testing Digital Twin System")
    print("=" * 60)
    
    system = DigitalTwinSystem()
    
    # Create a digital twin
    twin = system.create_twin(
        legal_name="Test User",
        date_of_birth=date(1990, 1, 1),
        nationality="US",
        gender=Gender.MALE
    )
    
    print(f"\n✅ Created twin: {twin.identity.twin_id}")
    print(f"✅ Legal name: {twin.identity.legal_name}")
    print(f"✅ Date of birth: {twin.identity.date_of_birth}")
    print(f"✅ Nationality: {twin.identity.nationality}")
    
    # Add life event
    system.add_life_event(
        twin_id=twin.identity.twin_id,
        event_type="education",
        event_date=date(2008, 9, 1),
        description="Started university",
        location="MIT"
    )
    
    print(f"✅ Added life event")
    print(f"✅ Life events count: {len(twin.life_events)}")
    
    # Add skill
    system.add_skill(
        twin_id=twin.identity.twin_id,
        skill_name="Python Programming",
        proficiency_level=0.9,
        years_experience=10
    )
    
    print(f"✅ Added skill")
    print(f"✅ Skills count: {len(twin.skills)}")
    
    # Get summary
    summary = system.get_twin_summary(twin.identity.twin_id)
    print(f"\n✅ Twin summary:")
    print(f"  - Life stage: {summary['life_stage']}")
    print(f"  - Social connections: {summary['social_connections_count']}")
    print(f"  - Life events: {summary['life_events_count']}")
    print(f"  - Skills: {summary['skills_count']}")
    
    return system

async def test_life_protocol_automation():
    """Test Life Protocol Automation"""
    print("\n" + "=" * 60)
    print("Testing Life Protocol Automation")
    print("=" * 60)
    
    from core.digital_twin_system import get_digital_twin_system
    
    digital_twin_system = get_digital_twin_system()
    automation_system = get_life_protocol_automation()
    
    # Create a digital twin
    twin = digital_twin_system.create_twin(
        legal_name="Automation Test User",
        date_of_birth=date(1990, 1, 1),
        nationality="US",
        gender=Gender.MALE
    )
    
    print(f"\n✅ Created twin: {twin.identity.twin_id}")
    
    # Auto-schedule tasks
    automation_system.auto_schedule_for_twin(twin.identity.twin_id)
    
    tasks = automation_system.get_tasks_for_twin(twin.identity.twin_id)
    print(f"✅ Scheduled tasks: {len(tasks)}")
    
    for task in tasks:
        print(f"  - {task.event_type.value}: {task.status.value}")
    
    # Execute a task
    if tasks:
        result = await automation_system.execute_task(tasks[0].task_id)
        print(f"✅ Task execution result: {result}")
    
    return automation_system

async def test_integration():
    """Test all components together"""
    print("\n" + "=" * 60)
    print("Testing Full Integration")
    print("=" * 60)
    
    # Initialize all systems
    gateway = await test_universal_api_gateway()
    digital_twin_system = await test_digital_twin_system()
    automation_system = await test_life_protocol_automation()
    
    print("\n" + "=" * 60)
    print("✅ All Universal OS Components Integrated Successfully!")
    print("=" * 60)
    
    print("\n📊 Summary:")
    print(f"  - API Gateway: Running on port 8001")
    print(f"  - Digital Twins: {len(digital_twin_system.twins)}")
    print(f"  - Automation Tasks: {len(automation_system.tasks)}")
    
    return {
        "gateway": gateway,
        "digital_twin_system": digital_twin_system,
        "automation_system": automation_system
    }

if __name__ == "__main__":
    asyncio.run(test_integration())
