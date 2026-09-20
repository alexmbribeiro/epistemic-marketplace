import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CognitiveAgent(Base):
    __tablename__ = "cognitive_agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    archetype: Mapped[str] = mapped_column(String(50), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    creator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    # Peer rating from debates. Deliberately does not feed the belief
    # aggregation: weighting the map of uncertainty by how well rival schools
    # rate you would be a different claim than this number supports.
    elo_rating: Mapped[float] = mapped_column(Float, default=1500.0)
    debates_judged: Mapped[int] = mapped_column(Integer, default=0)
    debates_rated_in: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", back_populates="agents")
    positions = relationship("AgentPosition", back_populates="agent")
    calibration_records = relationship("CalibrationRecord", back_populates="agent")
