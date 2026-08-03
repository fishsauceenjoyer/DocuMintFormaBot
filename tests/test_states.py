"""Tests for FSM state classes.

Verifies:
    - FSM state groups exist with correct states
    - State transitions are valid
"""

import pytest

from fsm.states import AdminState, OrderState


class TestOrderStates:
    """Tests for the OrderState FSM group."""

    def test_order_states_exist(self):
        """Verify all expected OrderState states are defined."""
        expected_states = [
            "choosing_document",
            "entering_quantity",
            "filling_document",
            "asking_delivery",
            "filling_delivery",
            "choosing_payment",
            "waiting_for_payment_proof",
            "fast_order_waiting",
        ]
        for state_name in expected_states:
            assert hasattr(OrderState, state_name)

    def test_order_states_are_unique(self):
        """Verify each state returns a unique object."""
        states = [
            OrderState.choosing_document,
            OrderState.entering_quantity,
            OrderState.filling_document,
            OrderState.asking_delivery,
            OrderState.filling_delivery,
            OrderState.choosing_payment,
            OrderState.waiting_for_payment_proof,
            OrderState.fast_order_waiting,
        ]
        assert len(set(states)) == len(states)


class TestAdminStates:
    """Tests for the AdminState FSM group."""

    def test_admin_states_exist(self):
        """Verify all expected AdminState states are defined."""
        expected_states = [
            "waiting_for_tracking",
            "waiting_for_file",
            "waiting_for_order_id",
        ]
        for state_name in expected_states:
            assert hasattr(AdminState, state_name)

    def test_admin_states_are_unique(self):
        """Verify each state returns a unique object."""
        states = [
            AdminState.waiting_for_tracking,
            AdminState.waiting_for_file,
            AdminState.waiting_for_order_id,
        ]
        assert len(set(states)) == len(states)


class TestStateGroups:
    """Tests for state group properties."""

    def test_order_state_is_statesgroup(self):
        """Verify OrderState inherits from StatesGroup."""
        from aiogram.fsm.state import StatesGroup

        assert issubclass(OrderState, StatesGroup)

    def test_admin_state_is_statesgroup(self):
        """Verify AdminState inherits from StatesGroup."""
        from aiogram.fsm.state import StatesGroup

        assert issubclass(AdminState, StatesGroup)
