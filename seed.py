#!/usr/bin/env python
"""Seed script for EthosOS development.

Creates example portfolio → program → project → sprint.
"""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from uuid import uuid4
from ethos_os.db import get_session, create_tables
from ethos_os.repositories import (
    PortfolioRepository,
    ProgramRepository,
    ProjectRepository,
    SprintRepository,
    PRDRepository,
)
from ethos_os.models.project import ProjectStatus
from ethos_os.models.prd import PRDStatus


def seed(session):
    """Create seed data."""
    print("Creating seed data...")
    
    # Create portfolio
    portfolio = PortfolioRepository(session).create({
        'name': 'Demo Corp',
        'strategic_intent': 'Revolutionize human-agent collaboration',
        'owner_id': None,
    })
    print(f"  Created: Portfolio {portfolio.name}")
    
    # Create program
    program = ProgramRepository(session).create({
        'name': 'EthosOS',
        'portfolio_id': portfolio.id,
        'description': 'The flagship initiative',
        'owner_id': None,
    })
    print(f"  Created: Program {program.name}")
    
    # Create project
    project = ProjectRepository(session).create({
        'name': 'v0.1 MVP',
        'program_id': program.id,
        'intent': 'Ship core initiative hierarchy',
        'success_metric': 'Portfolio → task traversal works',
        'scope': 'Domain models, working memory, no API',
        'boundaries': 'No API, no heartbeat, no gates',
        'timeline': '{"start": "2026-04-24", "end": "2026-05-01", "milestones": []}',
        'budget': 1000000,  # $10,000
        'prd_status': ProjectStatus.APPROVED.value,  # Pre-approved for demo
        'owner_id': None,
    })
    print(f"  Created: Project {project.name} (status: {project.prd_status})")
    
    # Create PRD for project
    prd = PRDRepository(session).create({
        'project_id': project.id,
        'intent': 'Ship core initiative hierarchy',
        'success_metric': 'Portfolio → task traversal works',
        'scope': 'Domain models, working memory, no API',
        'boundaries': 'No API, no heartbeat, no gates',
        'budget': 1000000,
        'status': PRDStatus.APPROVED.value,
    })
    print(f"  Created: PRD for {project.name}")
    
    # Create sprint
    sprint = SprintRepository(session).create({
        'name': 'Sprint 1',
        'project_id': project.id,
        'goal': 'Get domain models working',
        'start_date': '2026-04-24',
        'end_date': '2026-05-01',
        'capacity_hours': 80,
        'status': 'active',
        'owner_id': None,
    })
    print(f"  Created: Sprint {sprint.name}")
    
    print()
    print(f"Complete: {portfolio.name} → {program.name} → {project.name} → {sprint.name}")
    
    return portfolio, program, project, sprint


if __name__ == '__main__':
    # Create tables first
    create_tables()
    print("Tables created.")
    
    # Seed data
    with get_session() as session:
        seed(session)
    
    print("Seed complete!")