"""update predictions

Revision ID: 20240320_update_predictions
Revises: previous_revision
Create Date: 2024-03-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '20240320_update_predictions'
down_revision = 'previous_revision'  # Update this to your previous migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop the old first_pit_driver column
    op.drop_column('user_predictions', 'first_pit_driver')
    
    # Add new prediction columns
    op.add_column('user_predictions',
        sa.Column('most_pit_stops_driver', sa.Integer(), nullable=False)
    )
    op.add_column('user_predictions',
        sa.Column('most_positions_gained', sa.Integer(), nullable=False)
    )
    
    # Update prediction scores table
    op.drop_column('prediction_scores', 'first_pit_score')
    op.add_column('prediction_scores',
        sa.Column('most_pit_stops_score', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column('prediction_scores',
        sa.Column('most_positions_gained_score', sa.Integer(), nullable=False, server_default='0')
    )

def downgrade() -> None:
    # Remove new columns
    op.drop_column('prediction_scores', 'most_positions_gained_score')
    op.drop_column('prediction_scores', 'most_pit_stops_score')
    op.add_column('prediction_scores',
        sa.Column('first_pit_score', sa.Integer(), nullable=False, server_default='0')
    )
    
    # Restore original prediction columns
    op.drop_column('user_predictions', 'most_positions_gained')
    op.drop_column('user_predictions', 'most_pit_stops_driver')
    op.add_column('user_predictions',
        sa.Column('first_pit_driver', sa.Integer(), nullable=False)
    ) 