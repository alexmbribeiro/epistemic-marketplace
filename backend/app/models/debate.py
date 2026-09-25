import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Debate(Base):
    __tablename__ = "debates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="initializing")
    # Whether this debate counts toward the Elo and the per-agent statistics.
    # A public visitor gets the whole experience — the rounds, the jury, the
    # scores, all stored — but an open site would otherwise let anyone reshape
    # the ranking by running twenty debates with their favourite, and the
    # corpus is only meaningful because participation is balanced.
    ranked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    agent_ids: Mapped[list] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    final_belief_distribution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    argument_graph: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    unknown_unknowns: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    # {conclusion, trajectory, exchanges} — what the rounds add up to, beyond the number.
    synthesis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    claim = relationship("Claim", back_populates="debates")

    @property
    def claim_content(self) -> str | None:
        """Requires the claim to have been eager-loaded; a lazy load would
        raise inside an async session."""
        return self.claim.content if self.claim else None

    @property
    def claim_category(self) -> str | None:
        return self.claim.category if self.claim else None
    positions = relationship("AgentPosition", back_populates="debate")
    arguments = relationship("Argument", back_populates="debate")


class AgentPosition(Base):
    __tablename__ = "agent_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("debates.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cognitive_agents.id"), nullable=False)
    belief_score: Mapped[float] = mapped_column(Float, nullable=False)
    probability_true: Mapped[float] = mapped_column(Float, nullable=False, server_default='0.5')
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


class JuryRating(Base):
    """One judge's verdict on one participant of one debate.

    Judges are drawn from philosophers who did not take part, so nobody rates
    themselves. Scores are on craft, not agreement — see the judge prompt.
    """

    __tablename__ = "jury_ratings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("debates.id"), nullable=False)
    judge_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cognitive_agents.id"), nullable=False)
    subject_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cognitive_agents.id"), nullable=False)
    method_fidelity: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement: Mapped[int] = mapped_column(Integer, nullable=False)
    crux_quality: Mapped[int] = mapped_column(Integer, nullable=False)
    responsiveness: Mapped[int] = mapped_column(Integer, nullable=False)
    overall: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
