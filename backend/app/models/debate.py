import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Debate(Base):
    __tablename__ = "debates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="initializing")
    agent_ids: Mapped[list] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    final_belief_distribution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    argument_graph: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    unknown_unknowns: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    claim = relationship("Claim", back_populates="debates")
    positions = relationship("AgentPosition", back_populates="debate")
    arguments = relationship("Argument", back_populates="debate")


class AgentPosition(Base):
    __tablename__ = "agent_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("debates.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cognitive_agents.id"), nullable=False)
    belief_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_low: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_high: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    key_evidence: Mapped[list] = mapped_column(ARRAY(Text), default=list)
    cruxes: Mapped[list] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    debate = relationship("Debate", back_populates="positions")
    agent = relationship("CognitiveAgent", back_populates="positions")


class Argument(Base):
    __tablename__ = "arguments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("debates.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cognitive_agents.id"), nullable=False)
    target_argument_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("arguments.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    strength: Mapped[float] = mapped_column(Float, default=0.5)

    debate = relationship("Debate", back_populates="arguments")


class CalibrationRecord(Base):
    __tablename__ = "calibration_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cognitive_agents.id"), nullable=False)
    predicted_belief: Mapped[float] = mapped_column(Float, nullable=False)
    actual_outcome: Mapped[float | None] = mapped_column(Float, nullable=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    claim = relationship("Claim", back_populates="calibration_records")
    agent = relationship("CognitiveAgent", back_populates="calibration_records")
