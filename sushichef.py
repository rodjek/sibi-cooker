#!/usr/bin/env python

import csv
from pathlib import Path
from ricecooker.chefs import SushiChef
from ricecooker.classes.files import DocumentFile, AudioFile
from ricecooker.classes.licenses import get_license
from ricecooker.classes.nodes import ChannelNode, DocumentNode, TopicNode, AudioNode
import yaml


class TIBChef(SushiChef):
    def get_channel(self, **kwargs):
        return ChannelNode(
            source_id=kwargs["yaml_data"]["channel"]["source"]["id"],
            source_domain=kwargs["yaml_data"]["channel"]["source"]["domain"],
            title=kwargs["yaml_data"]["channel"]["title"],
            description=kwargs["yaml_data"]["channel"]["description"],
            thumbnail=kwargs["yaml_data"]["channel"]["thumbnail"],
            language=kwargs["yaml_data"]["channel"]["language"],
        )

    def get_topics(self, channel, yaml_data):
        topics = {}

        for top_level in yaml_data["topics"]:
            topics[top_level["key"]] = TopicNode(
                title=top_level["title"],
                source_id=top_level["id"],
                derive_thumbnail=True,
            )
            for sub_topic in top_level["children"]:
                sub_key = top_level["key"] + sub_topic["key"]
                topics[sub_key] = TopicNode(
                    title=sub_topic["title"],
                    source_id=sub_topic["id"],
                    derive_thumbnail=True,
                )
                topics[top_level["key"]].add_child(topics[sub_key])
            channel.add_child(topics[top_level["key"]])
        return topics

    def construct_channel(self, **kwargs):
        with open("data.yml", "r") as file:
            yaml_data = yaml.safe_load(file)

        channel = self.get_channel(**kwargs, yaml_data=yaml_data)
        topics = self.get_topics(channel, yaml_data)

        book_list = Path(yaml_data["book_list_path"]).resolve()
        with book_list.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Type"] == "PDF":
                    if row["Category"] == "Non-text":
                        key = row["Level"]
                    else:
                        key = row["Class"]

                    document_node = DocumentNode(
                        title=row["Book List Title"],
                        description=row["Book List Title"],
                        source_id="sibi/" + row["Category"] + "/" + row["File Name"],
                        license=get_license(
                            yaml_data["license"]["type"],
                            copyright_holder=yaml_data["license"]["copyright_holder"],
                            description=yaml_data["license"]["description"],
                        ),
                        language="id",
                        derive_thumbnail=True,
                        files=[
                            DocumentFile(
                                path=str(Path(yaml_data["books_path"]).resolve() / key / row["File Name"]),
                                language="id",
                            ),
                        ]
                    )
                    topics[row["Category"] + key].add_child(document_node)
                else:
                    key = row["Class"]
                    file_list = Path(yaml_data["audio_books_path"]).resolve() / key / row["File Name"] / "files.csv"
                    audio_book = TopicNode(
                        title=row["Book List Title"],
                        source_id="sibi/" + row["Category"] + "/" + row["File Name"],
                        derive_thumbnail=True,
                    )
                    with file_list.open(newline="", encoding="utf-8") as audiocsv:
                        audioreader = csv.DictReader(audiocsv)
                        for audiorow in audioreader:
                            audio_node = AudioNode(
                                title=audiorow["Title"],
                                description=audiorow["Title"],
                                source_id="sibi/" + row["Category"] + "/" + row["File Name"] + audiorow["File Name"],
                                license=get_license(
                                    yaml_data["license"]["type"],
                                    copyright_holder=yaml_data["license"]["copyright_holder"],
                                    description=yaml_data["license"]["description"],
                                ),
                                language="id",
                                files=[
                                    AudioFile(
                                        path=str(Path(yaml_data["audio_books_path"]).resolve() / key / row["File Name"] / audiorow["File Name"]),
                                        language="id",
                                    ),
                                ],
                            )
                            audio_book.add_child(audio_node)
                        topics[row["Category"] + key].add_child(audio_book)

        return channel


if __name__ == "__main__":
    tib_chef = TIBChef()
    tib_chef.main()
