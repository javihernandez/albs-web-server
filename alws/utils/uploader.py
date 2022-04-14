import io
import re
import typing
import urllib.parse

from alws.config import settings
from alws.utils.ids import get_random_unique_version
from alws.utils.modularity import IndexWrapper
from alws.utils.pulp_client import PulpClient


class MetadataUploader:
    def __init__(self):
        self.pulp = PulpClient(settings.pulp_host, settings.pulp_user,
                               settings.pulp_password)

    async def upload_comps(self, repo_href: str, comps_content: str) -> None:
        data = {
            'file': io.StringIO(comps_content),
            'repository': repo_href,
            'replace': 'true',
        }
        await self.pulp.upload_comps(data)

    async def upload_modules(self, repo_href: str,
                             module_content: str) -> (str, typing.List[str]):
        latest_repo_href = await self.pulp.get_repo_latest_version(repo_href)
        latest_repo_data = await self.pulp.get_latest_repo_present_content(
            latest_repo_href)
        module_content_keys = ('rpm.modulemd_defaults', 'rpm.modulemd')
        repo_data_hrefs = [
            latest_repo_data.get(key, {}).get('href')
            for key in module_content_keys
        ]
        repo_modules_to_remove = []
        for repo_type_href in repo_data_hrefs:
            if repo_type_href is None:
                continue
            repo_modules_to_remove.extend([
                content['pulp_href']
                async for content in self.pulp.iter_repo(repo_type_href)
            ])
        artifact_href, _ = await self.pulp.upload_file(module_content)
        _index = IndexWrapper.from_template(module_content)
        module = next(_index.iter_modules())
        payload = {
            'relative_path': 'modules.yaml',
            'artifact': artifact_href,
            'name': module.name,
            'stream': module.stream,
            'version': get_random_unique_version(),
            'context': module.context,
            'arch': module.arch,
            'artifacts': [],
            'dependencies': [],
        }
        module_to_add = await self.pulp.create_module_by_payload(payload)
        return module_to_add, repo_modules_to_remove

    async def process_uploaded_files(
        self,
        repo_name: str,
        module_content: bytes = None,
        comps_content: bytes = None,
    ) -> typing.List[str]:
        repo = await self.pulp.get_rpm_repository_by_params({
            'name__contains': repo_name})
        repo_href = repo['pulp_href']
        content_to_add = []
        content_to_remove = []
        updated_metadata = []
        if module_content is not None:
            module_content = await module_content.read()
            module_to_add, modules_to_remove = await self.upload_modules(
                repo_href, module_content.decode())
            content_to_add.append(module_to_add)
            content_to_remove.extend(modules_to_remove)
            updated_metadata.append('modules.yaml')
        if comps_content is not None:
            comps_content = await comps_content.read()
            await self.upload_comps(repo_href, comps_content.decode())
            updated_metadata.append('comps.xml')
        await self.pulp.modify_repository(repo_href, add=content_to_add,
                                          remove=content_to_remove)
        await self.pulp.create_rpm_publication(repo_href)
        return updated_metadata
