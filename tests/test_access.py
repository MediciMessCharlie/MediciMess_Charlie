"""Tests for Phase 7 role-based authorization rules."""

from dashboard.access import Role, UserAccess, can_view_branch, can_view_network


def test_managing_director_can_view_network_and_every_branch():
    user = UserAccess("lorenzo", Role.MANAGING_DIRECTOR)

    assert can_view_network(user)
    assert can_view_branch(user, "Florence")
    assert can_view_branch(user, "Rome")


def test_branch_manager_can_view_only_assigned_branch():
    user = UserAccess("rome.manager", Role.BRANCH_MANAGER, branch="Rome")

    assert not can_view_network(user)
    assert can_view_branch(user, "Rome")
    assert not can_view_branch(user, "Florence")
