import re
import bz2
import urllib.parse
import tempfile
import collections
from typing import List

import aiohttp

from alws.scripts.oval_cacher.schema import (
    CVE,
    CVRF,
    OvalGenericInfo,
    OvalDefinition,
)
from almalinux.liboval.composer import Composer


def oval_to_dict(oval_content) -> dict:
    with tempfile.NamedTemporaryFile("wb") as fd:
        fd.write(bz2.decompress(oval_content))
        fd.flush()
        return Composer.load_from_file(fd.name).as_dict()


class SecurityApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.oval_list_endpoint = urllib.parse.urljoin(base_url, "oval.json")

    async def make_request(self, request):
        async with request as response:
            response.raise_for_status()
            return await response.json()

    async def iter_oval_items(self) -> List[OvalGenericInfo]:
        page = 1
        while True:
            items = await self.make_request(
                aiohttp.request(
                    "get", self.oval_list_endpoint, params={"page": page}
                )
            )
            if not items:
                return
            for item in items:
                yield OvalGenericInfo(**item)
            page += 1

    async def get_full_oval_info(
        self, oval_item: OvalGenericInfo
    ) -> OvalDefinition:
        request = aiohttp.request("get", oval_item.resource_url)
        response = (await self.make_request(request))["oval_definitions"]
        definition = response.pop("definitions")["definition"]
        objects = response.pop("objects").get("rpminfo_object", [])
        states = response.pop("states").get("rpminfo_state", [])
        tests = response.pop("tests").get("rpminfo_test", [])
        advisory = definition["metadata"]["advisory"]
        advisory["affected_cpe_list"] = advisory["affected_cpe_list"].get(
            "cpe", []
        )
        return OvalDefinition(
            objects=objects,
            definition=definition,
            tests=tests,
            states=states,
            **response,
        )

    async def get_cve(self, cve_id: str):
        request = aiohttp.request(
            "get", urllib.parse.urljoin(self.base_url, f"cve/{cve_id}.json")
        )
        return CVE(**(await self.make_request(request)))

    async def get_cvrf(self, oval_item: OvalGenericInfo) -> CVRF:
        request = aiohttp.request(
            "get",
            urllib.parse.urljoin(self.base_url, f"cvrf/{oval_item.RHSA}.json"),
        )
        return CVRF(**(await self.make_request(request))["cvrfdoc"])

    def _get_record_id(self, definition: dict) -> str:
        def_id = re.search(
            r"^RH\w{2}-\d+:\d+", definition["metadata"]["title"]
        )
        if def_id:
            return def_id.group()
        for ref in definition["metadata"]["references"]:
            match = re.search(r"^(RH|AL)\w{2}-\d+:\d+", ref["id"])
            if match:
                result = match.group()
                return re.sub("^AL", "RH", result)
        raise ValueError("Unable to get definition id from: %s", definition)

    async def load_oval_xml_cache(self, distr_version: str) -> dict:
        distr_version_to_oval_xml_links = {
            "8": [
                "https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2",
                "https://repo.almalinux.org/security/oval/org.almalinux.alsa-8.xml.bz2",
            ],
            "9": [
                "https://www.redhat.com/security/data/oval/com.redhat.rhsa-RHEL9.xml.bz2",
                "https://repo.almalinux.org/security/oval/org.almalinux.alsa-9.xml.bz2",
            ],
        }
        result = collections.defaultdict(dict)
        for link in distr_version_to_oval_xml_links[distr_version]:
            async with aiohttp.request("get", link) as response:
                body = await response.content.read()
            dict_oval = oval_to_dict(body)
            for definition in dict_oval["definitions"]:
                definition["freezed_record"] = bool(
                    definition["metadata"]["title"].startswith("AL")
                )
                definition["metadata"]["title"] = re.sub(
                    "^AL", "RH", definition["metadata"]["title"]
                )
                def_id = self._get_record_id(definition)
                result["definitions"][def_id] = definition
            for key in ("tests", "objects", "states", "variables"):
                for item in dict_oval[key]:
                    result[key][item["id"]] = item
        return result