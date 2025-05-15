from datetime import datetime
from app import db

class Metal(db.Model):
    """Model for precious metals."""
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)  # e.g., 'GOLD', 'SILVER'
    name = db.Column(db.String(50), nullable=False)  # e.g., 'Gold', 'Silver'
    unit = db.Column(db.String(20), nullable=False)  # e.g., 'USD/oz', 'USD/kg'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with prices
    prices = db.relationship('MetalPrice', backref='metal', lazy='dynamic')

    def __repr__(self):
        return f'<Metal {self.symbol}>'

class MetalPrice(db.Model):
    """Model for storing metal prices."""
    id = db.Column(db.Integer, primary_key=True)
    metal_id = db.Column(db.Integer, db.ForeignKey('metal.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MetalPrice {self.metal_id} at {self.timestamp}>'

class MetalAnalysis(db.Model):
    """Model for storing metal price analysis."""
    id = db.Column(db.Integer, primary_key=True)
    metal_id = db.Column(db.Integer, db.ForeignKey('metal.id'), nullable=False)
    trend = db.Column(db.String(20), nullable=False)  # 'up', 'down', 'unchanged'
    volatility = db.Column(db.String(20), nullable=False)  # 'high', 'medium', 'low'
    sentiment = db.Column(db.String(20), nullable=False)  # 'positive', 'negative', 'neutral'
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MetalAnalysis {self.metal_id} for {self.period_start} to {self.period_end}>' 