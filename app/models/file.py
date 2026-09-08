from pathlib import Path
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

from app.core.config import settings

def get_class_icon(name):
    match Path(name).suffix:
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
        case '.doc' | '.docx' | '.ppt' | '.pptx' | '.xls' | '.xlsx':
            return 'text','file-document'
        case '.mp4' | '.mkv':
            return 'info','file-video'
        case '.mp3' | '.wav':
            return 'info', 'file-music'
        case '.jpg' | '.jpeg' | '.gif' | '.png':
            return 'warning','file-image'
        case _:
            return 'secondary','file'

class File(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=200,default=None,description="Name file. Needed to show it in Sake")
    permanent_link: str = Field(max_length=200,default=None,description="Permanent link in Synology Drive")
    record_id: int | None = Field(default=None,foreign_key="record.id",description="This file belongs to record_id")
    to_delete: bool | None = Field(default=False)
    created_at: datetime | None = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default_factory=datetime.utcnow)

    #record: "Record" = Relationship(back_populates="files")

    @property
    def link(self):
        return f"https://{settings.SYNOLOGY_SERVER}:{settings.SYNOLOGY_PORT}/oo/r/{self.permanent_link}"

    @property
    def icon(self):
        return get_class_icon(self.name)

    @property
    def short_name(self):
        limit = 20
        if len(self.name) > limit:
            return f'{self.name[:limit-3]}...'
        return self.name

    @property
    def html_name(self):
        rst = f"""
            <span class="icon">
                <span class="iconify has-text-{self.icon[0]}" data-icon="mdi-{self.icon[1]}"></span>
            </span>
            <span>
                { self.name }
            </span>
              """
        return rst

    @property
    def html_icon(self):
        rst = f"""
            <span class="icon is-small">
                <span class="iconify has-text-{self.icon[0]}" data-width="1.2em" data-icon="mdi-{self.icon[1]}"></span>
            </span>
              """

        return rst

    @property
    def shorter_name(self):
        limit = 14
        if len(self.name) > limit:
            return f'{self.name[:limit-3]}...'
        return self.name

    @property
    def html_name_short(self):
        rst = f"""
            <span class="icon">
                <span class="iconify has-text-{self.icon[0]}" data-icon="mdi-{self.icon[1]}"></span>
            </span>
            <span>
                { self.shorter_name }
            </span>
              """
        return rst
