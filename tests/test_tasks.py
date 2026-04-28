from httpx import AsyncClient

from tests.conftest import create_project, create_workspace, register_user


async def test_task_crud_filters_and_assignment_job(
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

    task = await client.post(
        f"/api/v1/workspaces/{workspace['id']}/tasks",
        headers=auth_headers(owner["access_token"]),
        json={
            "project_id": project["id"],
            "title": "Send launch checklist",
            "status": "todo",
            "due_date": "2026-05-10",
            "assigned_to_id": member["user"]["id"],
        },
    )
    assert task.status_code == 201, task.text
    assert task.json()["assigned_to_id"] == member["user"]["id"]

    filtered = await client.get(
        f"/api/v1/workspaces/{workspace['id']}/tasks",
        headers=auth_headers(owner["access_token"]),
        params={
            "status": "todo",
            "project_id": project["id"],
            "assigned_to_id": member["user"]["id"],
        },
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1

    updated = await client.patch(
        f"/api/v1/workspaces/{workspace['id']}/tasks/{task.json()['id']}",
        headers=auth_headers(member["access_token"]),
        json={"status": "in_progress"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"

    deleted = await client.delete(
        f"/api/v1/workspaces/{workspace['id']}/tasks/{task.json()['id']}",
        headers=auth_headers(owner["access_token"]),
    )
    assert deleted.status_code == 200


async def test_task_assignee_must_belong_to_workspace(
    client: AsyncClient,
    auth_headers,
) -> None:
    owner = await register_user(client, email="owner@example.com")
    outsider = await register_user(client, email="outsider@example.com")
    workspace = await create_workspace(client, owner["access_token"])
    project = await create_project(client, owner["access_token"], workspace["id"])

    response = await client.post(
        f"/api/v1/workspaces/{workspace['id']}/tasks",
        headers=auth_headers(owner["access_token"]),
        json={
            "project_id": project["id"],
            "title": "Assign outside user",
            "assigned_to_id": outsider["user"]["id"],
        },
    )

    assert response.status_code == 422
