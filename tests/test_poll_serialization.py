from threading import Event, Thread, current_thread
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from custom_components.icloud3 import icloud3_main


class _StopAfterPrefetch(BaseException):
    """Exit the synthetic tick before it reads or writes device state."""


class PollSerializationTests(unittest.TestCase):
    def test_next_tick_cannot_enter_tracking_while_midnight_renewal_is_running(self):
        renewal_started = Event()
        finish_renewal = Event()
        prefetch_calls = []
        worker_errors = []

        def midnight_maintenance():
            renewal_started.set()
            if not finish_renewal.wait(3):
                raise TimeoutError("test did not release midnight maintenance")

        def prefetch():
            prefetch_calls.append(current_thread().name)
            raise _StopAfterPrefetch

        def clock():
            return "00:15:00" if current_thread().name == "midnight" else "00:15:05"

        gb = SimpleNamespace(
            InternetError=SimpleNamespace(internet_error_test_timeout=False, internet_error_secs=0),
            internet_error=False,
            icloud_io_request_secs=0,
            was_icloud3_restart_requested=False,
            config_parms_update_control=[],
            conf_devices=[object()],
            evlog_action_request="",
            is_all_tracking_paused=False,
            EvLog=SimpleNamespace(clear_secs=1),
            device_mobapp_verify_retry_needed=False,
            conf_data_source_MOBAPP=False,
            AppleAcct_error_by_apple_id={},
            is_log_level_debug=False,
        )
        with patch.object(icloud3_main, "Gb", gb), patch.object(
            icloud3_main.uach, "update_auth_entities_state"
        ), patch.object(icloud3_main, "secs_since", return_value=0), patch.object(
            icloud3_main, "time_now", side_effect=clock
        ), patch.object(icloud3_main, "time_now_secs", return_value=0), patch.object(
            icloud3_main.det_interval, "set_dist_to_devices"
        ):
            controller = icloud3_main.iCloud3()
            controller._check_mobappp_location_request = Mock()
            controller._timer_tasks_midnight = midnight_maintenance
            controller._main_5sec_loop_icloud_prefetch_control = prefetch

            def tick():
                try:
                    controller.master_5sec_interval_handler(None)
                except _StopAfterPrefetch:
                    pass
                except BaseException as error:
                    worker_errors.append(error)

            midnight = Thread(target=tick, name="midnight", daemon=True)
            midnight.start()
            try:
                self.assertTrue(renewal_started.wait(3))
                tick()
                self.assertEqual(prefetch_calls, [])
            finally:
                finish_renewal.set()
                midnight.join(3)

            self.assertFalse(midnight.is_alive())
            self.assertEqual(worker_errors, [])
            self.assertEqual(prefetch_calls, ["midnight"])

            # The synthetic stop bypasses the standard tracking flag cleanup.
            controller.initialize_5_sec_loop_control_flags()
            tick()
            self.assertEqual(prefetch_calls, ["midnight", current_thread().name])
