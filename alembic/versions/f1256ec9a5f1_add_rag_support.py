"""add_rag_support

Revision ID: f1256ec9a5f1
Revises: 8a9e3f328c1e
Create Date: 2025-10-13 07:51:50.918566

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f1256ec9a5f1'
down_revision: Union[str, Sequence[str], None] = '8a9e3f328c1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - dodaj RAG support."""
    # Tabela RAG documents
    op.create_table('rag_documents',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.String(length=512), nullable=False),
    sa.Column('file_type', sa.String(length=50), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('date', sa.Float(), nullable=True),
    sa.Column('num_chunks', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('status', sa.String(length=50), server_default=sa.text("'processing'"), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    # Dodaj indeksy dla rag_documents
    op.create_index('ix_rag_documents_status', 'rag_documents', ['status'])
    op.create_index('ix_rag_documents_is_active', 'rag_documents', ['is_active'])

    # Dodaj pola RAG do personas
    op.add_column('personas',
        sa.Column('rag_context_used', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    op.add_column('personas',
        sa.Column('rag_citations', postgresql.JSONB(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema - usuń RAG support."""
    # Usuń pola RAG z personas
    op.drop_column('personas', 'rag_citations')
    op.drop_column('personas', 'rag_context_used')

    # Usuń indeksy z rag_documents
    op.drop_index('ix_rag_documents_is_active', table_name='rag_documents')
    op.drop_index('ix_rag_documents_status', table_name='rag_documents')

    # Usuń tabelę rag_documents
    op.drop_table('rag_documents')
