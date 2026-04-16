from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from DAO.db import Base

class Servicio(Base):
    __tablename__ = 'servicios'

    id_servicio = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, ForeignKey('categorias_servicio.id_categoria'))
    nombre_servicio = Column(String(100), nullable=False)
    precio = Column(Numeric(10, 2))
    duracion_minutos = Column(Integer)

    categoria = relationship("CategoriaServicio", back_populates="servicios")
    detalles = relationship("DetalleCita", back_populates="servicio")