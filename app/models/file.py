from pathlib import Path
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class File(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=200,default=None,description="Name file. Needed to show it in Sake")
    permanent_link: str = Field(max_length=200,default=None,description="Permanent link in Synology Drive")
    record_id: int | None = Field(default=None,foreign_key="record.id",description="This file belongs to record_id")
    to_delete: bool | None = Field(default=False)
    created_at: datetime | None = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default_factory=datetime.utcnow)

    record: "Record" = Relationship(back_populates="files")

    @property
    def icon(self):
        match Path(self.name).suffix:
            case '.osheet':
                return 'primary','file-excel'
            case '.odoc':
                return 'link','file-word'
            case '.oslides':
                return 'warning','file-powerpoint'
            case '.pdf':
                return 'danger','file-pdf'
            case '': # Folder
                return '',''
            case 'doc' | 'docx' | 'ppt' | 'pptx' | 'xls' | 'xlsx':
                return 'text','file-document'
            case 'mp4' | 'mkv':
                return 'info','file-video'
            case 'mp3' | 'wav':
                return 'info', 'file-music'
            case 'jpg' | 'gif' | 'png':
                return 'warning','file-image'
            case _:
                return '',''


