from httpx import AsyncClient

from tests.conftest import create_project, create_workspace, register_user


async def test_outsider_cannot_access_workspace_resources(
    client: AsyncClient,
    auth_headers,
) -> None:
    owner = await register_user(client, email="owner@example.com")
    outsider = await register_user(client, email="outsider@example.com")
    workspace = await create_workspace(client, owner["access_token"])

    response = await client.get(
        f"/api/v1/workspaces/{workspace['id']}/projects",
        headers=auth_headers(outsider["access_token"]),
    )

    assert response.status_code == 403


async def test_member_can_update_tasks_but_cannot_manage_projects(
    client: AsyncClient,
    auth_headers,
) -> None:
    owner = await register_user(client, email="owner@example.com")
    member = await register_user(client, email="member@example.com")
    workspace = await create_workspace(client, owner["access_token"])
    project = await create_project(client, owner["access_token"], workspace["id"])

    invite = await client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner["access_token"]),
        json={"email": "member@example.com", "role": "member"},
    )
    assert invite.status_code == 201

    blocked = await client.post(
        f"/api/v1/workspaces/{workspace['id']}/projects",
        headers=auth_headers(member["access_token"]),
        json={"name": "Member Project"},
    )
    assert blocked.status_code == 403

    created_task = await client.post(
        f"/api/v1/workspaces/{workspace['id']}/tasks",
        headers=auth_headers(member["access_token"]),
        json={"project_id": project["id"], "title": "Member created task"},
    )
    assert created_task.status_code == 201

    updated_task = await client.patch(
        f"/api/v1/workspaces/{workspace['id']}/tasks/{created_task.json()['id']}",
        headers=auth_headers(member["access_token"]),
        json={"status": "done"},
    )
    assert updated_task.status_code == 200
    assert updated_task.json()["status"] == "done"
