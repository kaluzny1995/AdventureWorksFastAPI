import json
from pydantic import BaseModel
from typing import List, Union


class Contact(BaseModel):
    name: str
    url: str
    email: str

    class Config:
        frozen = True


class LicenseInfo(BaseModel):
    name: str
    identifier: str

    class Config:
        frozen = True


class AppMetadataConfig(BaseModel):
    title: str
    description: str
    summary: str
    version: str
    contact: Contact
    license_info: LicenseInfo

    class Config:
        frozen = True

    @staticmethod
    def from_json() -> 'AppMetadataConfig':
        with open("metadata.json", "r") as f:
            config_dict = json.load(f)
        config_dict['description'] = "\n".join(config_dict['description'])
        config = AppMetadataConfig(**config_dict)
        return config
