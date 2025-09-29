"""Add Hunter.io enrichment support

Revision ID: add_hunter_enrichment
Revises: 871657416437
Create Date: 2025-09-28 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_hunter_enrichment'
down_revision = '871657416437'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if enriched_at column exists, if not add it
    # Add missing columns for Hunter.io enrichment
    try:
        op.add_column('leads', sa.Column('enriched_at', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Column already exists
    
    try:
        op.add_column('leads', sa.Column('hunter_data', sa.Text(), nullable=True))
    except Exception:
        pass  # Column already exists
    
    # Create hunter_log table for tracking API usage and rate limiting
    try:
        op.create_table(
            'hunter_log',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('domain', sa.String(255), nullable=False),
            sa.Column('emails_found', sa.Integer(), nullable=False, default=0),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('response_data', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.Index('idx_hunter_log_domain', 'domain'),
            sa.Index('idx_hunter_log_created_at', 'created_at')
        )
    except Exception:
        pass  # Table already exists
    
    # Add indexes for better query performance (only if they don't exist)
    try:
        op.create_index('idx_leads_domain', 'leads', ['domain'])
    except Exception:
        pass  # Index already exists
    
    try:
        op.create_index('idx_leads_email_null', 'leads', ['email'], postgresql_where=sa.text('email IS NULL'))
    except Exception:
        pass  # Index already exists
    
    try:
        op.create_index('idx_leads_enriched_at', 'leads', ['enriched_at'])
    except Exception:
        pass  # Index already exists
    
    try:
        op.create_index('idx_leads_verified', 'leads', ['verified'])
    except Exception:
        pass  # Index already exists
    
    try:
        op.create_index('idx_leads_confidence', 'leads', ['confidence'])
    except Exception:
        pass  # Index already exists


def downgrade() -> None:
    # Remove indexes (ignore errors if they don't exist)
    try:
        op.drop_index('idx_leads_confidence')
    except Exception:
        pass
    try:
        op.drop_index('idx_leads_verified')
    except Exception:
        pass
    try:
        op.drop_index('idx_leads_enriched_at')
    except Exception:
        pass
    try:
        op.drop_index('idx_leads_email_null')
    except Exception:
        pass
    try:
        op.drop_index('idx_leads_domain')
    except Exception:
        pass
    
    # Drop hunter_log table
    try:
        op.drop_table('hunter_log')
    except Exception:
        pass
    
    # Remove columns from leads table (only the ones we might have added)
    try:
        op.drop_column('leads', 'hunter_data')
    except Exception:
        pass
    try:
        op.drop_column('leads', 'enriched_at')
    except Exception:
        pass