"""add leagues

Revision ID: 20240320_add_leagues
Revises: 20240320_update_predictions
Create Date: 2024-03-20 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '20240320_add_leagues'
down_revision = '20240320_update_predictions'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create leagues table
    op.create_table(
        'leagues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('icon', sa.LargeBinary(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create league_members association table
    op.create_table(
        'league_members',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'league_id')
    )
    
    # Add foreign key to user_predictions table
    op.add_column('user_predictions',
        sa.Column('user_id', sa.Integer(), nullable=False)
    )
    op.create_foreign_key(
        'fk_user_predictions_user_id_users',
        'user_predictions', 'users',
        ['user_id'], ['id']
    )

def downgrade() -> None:
    # Remove foreign key from user_predictions
    op.drop_constraint('fk_user_predictions_user_id_users', 'user_predictions', type_='foreignkey')
    op.drop_column('user_predictions', 'user_id')
    
    # Drop tables in reverse order
    op.drop_table('league_members')
    op.drop_table('leagues')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users') 