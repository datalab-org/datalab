import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr

from pydatalab.models.entries import Entry


class Owner(BaseModel):

    ownerName: str
    """Full name of the owner"""

    ownerContact: Optional[EmailStr]
    """Contact address of the owner"""

    ownerIdentifier: Optional[str]
    """Identifier used to identify the owner"""

    ownerIdentifierType: Optional[str]
    """Type of the identifier"""


class Manufacturer(BaseModel):

    manufacturerName: str
    """Full name of the manufacturer"""

    manufacturerIdentifier: Optional[str]
    """Identifier used to identify the manufacturer"""

    manufacturerIdentifierType: Optional[str]
    """Type of the identifier"""


class InstrumentModelDetails(BaseModel):

    modelName: str
    """Full name of the model"""

    modelIdentifier: Optional[str]
    """Identifier used to identify the model"""

    modelIdentifierType: Optional[str]
    """Type of the identifier"""


class InstrumentType(BaseModel):

    instrumentTypeName: str
    """Full name of the instrument type"""

    instrumentTypeIdentifier: Optional[str]
    """Identifier used to identify the type of instrument"""

    instrumentTypeIdentifierType: Optional[str]
    """Type of the identifier"""


class RelatedIdentifier(BaseModel):
    relatedIdentifier: str
    """A related identifier"""

    relatedIdentifierType: Optional[str]
    """Type of the identifier.

    Controlled list of values:

        ARK, arXiv, bibcode, DOI, EAN13, EISSN, Handle, IGSN, ISBN, ISSN, ISTC, LISSN, PMID, PURL, RAiD, RRID, UPC, URL, URN, w3id

    """

    relationType: Optional[str]
    """Description of the relationship.

    Controlled list of values:

        IsDescribedBy, IsNewVersionOf, IsPreviousVersionOf, HasComponent, IsComponentOf, References, HasMetadata, WasUsedIn, IsIdenticalTo, IsAttachedTo

    """

    relatedIdentifierName: Optional[str]
    """A name for the related resource, may be used to give a hint on the content of that resource"""


class AlternateIdentifier(BaseModel):
    alternateIdentifier: str
    """An alternate identifier"""

    alternateIdentifierType: Optional[str]
    """Type of the identifier.

    Controlled list of values:

        SerialNumber, InventoryNumber, Other

    """

    alternateIdentifierName: Optional[str]
    """A supplementary name for the identifier type. This is mostly useful if alternateIdentifierType is Other."""


class PIDINSTInstrument(Entry):
    """An Instrument is a model that represents a physical instrument, based on
    the RDA PIDINST 1.0: https://doi.org/10.15497/RDA00070

    """

    type: Literal["instruments"] = "instruments"

    name: str
    """Name by which the instrument instance is known."""

    owner: List[Owner]
    """
    Institution(s) responsible for the management of the instrument.
    This may include the legal owner, the operator, or an institute providing access to the instrument.
    """

    manufacturer: List[Manufacturer]
    """
    The instrument's manufacturer(s) or developer.
    This may also be the owner for custom build instruments
    """

    model: List[InstrumentModelDetails]
    """Name of the model of type of device used in the instrument."""

    description: Optional[str]
    """Technical description of the device and its capabilities"""

    instrument_type: Optional[InstrumentType]
    """Classification of the type of the instrument"""

    measured_variable: Optional[List[str]]
    """The variable(s) that this instrument measures or observes"""

    date: Optional[List[datetime.date]]
    """Dates relevant to the instrument"""

    related_identifier: Optional[List[RelatedIdentifier]]
    """Identifiers of related resources"""

    alternate_identifier: Optional[List[AlternateIdentifier]]
    """Identifiers other than the PIDINST pertaining to the same instrument instance.
    This should be used if the instrument has a serial number.
    Other possible uses include an owner's inventory number or an entry in some instrument data base.
    """
