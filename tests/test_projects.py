from httpx import AsyncClient

from tests.conftest import create_project, create_workspace, register_user


async def test_project_crud_and_audit_logs(
    client: AsyncClient,
    auth_headers,
) -> None:
    auth = await register_user(client)
    workspace = await create_workspace(client, auth["access_token"])

    project = await create_project(client, auth["access_token"], workspace["id"])
    assert project["name"] == "Growth Launch"

    listing = await client.get(
        f"/api/v1/workspaces/{workspace['id']}/projects",
        headers=auth_headers(auth["access_token"]),
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    updated = await client.patch(
        f"/api/v1/workspaces/{workspace['id']}/projects/{project['id']}",
        headers=auth_headers(auth["access_token"]),
        json={"name": "Revenue Launch"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Revenue Launch"

    audit_logs = await client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(auth["access_token"]),
    )
    assert audit_logs.status_code == 200
    actions = {item["action"] for item in audit_logs.json()["items"]}
    assert {"workspace_created", "project_created", "project_updated"} <= actions

    deleted = await client.delete(
        f"/api/v1/workspaces/{workspace['id']}/projects/{project['id']}",
        headers=auth_headers(auth["access_token"]),
    )
    assert deleted.status_code == 200
