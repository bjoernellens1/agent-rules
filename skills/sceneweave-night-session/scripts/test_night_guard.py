import unittest
from datetime import datetime, timedelta, timezone
from night_guard import check


class NightGuardTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 11, 25, tzinfo=timezone.utc)
        self.ledger = {"start_utc": self.start.isoformat(), "wall_limit_min": 360,
                       "handover_reserve_min": 45, "gpu_limit_min": 180,
                       "gpu_allocated_min": 8.5, "tasks": [], "task_cap": 36}

    def task(self, id, status="pending", **kw):
        return {"id": id, "status": status, "estimated_wall_min": 20,
                "estimated_gpu_min": 5, **kw}

    def check_at(self, minutes):
        return check(self.ledger, self.start + timedelta(minutes=minutes))

    def test_early_finished_wave_does_not_allow_finish(self):
        self.ledger["tasks"] = [self.task("a", "done", outcome="screened"),
                                self.task("b", depends_on=["a"])]
        self.assertFalse(self.check_at(50)["finish_allowed"])
        self.assertEqual(self.check_at(50)["ready"], ["b"])

    def test_early_finish_requires_review(self):
        self.ledger["tasks"] = [self.task("a", "done", outcome="no further value")]
        self.assertFalse(self.check_at(50)["finish_allowed"])
        self.ledger["early_finish_backlog_review"] = "All authorized alternatives exhausted."
        self.assertTrue(self.check_at(50)["finish_allowed"])

    def test_gpu_exhausted_cpu_work_still_ready(self):
        self.ledger["gpu_allocated_min"] = 180
        self.ledger["tasks"] = [self.task("gpu"), self.task("cpu", estimated_gpu_min=0)]
        self.assertEqual(self.check_at(60)["ready"], ["cpu"])

    def test_handover_reserve(self):
        self.ledger["tasks"] = [self.task("a")]
        self.assertTrue(self.check_at(315)["finish_allowed"])

    def test_running_blocks_handover(self):
        self.ledger["tasks"] = [self.task("a", "running")]
        self.assertFalse(self.check_at(350)["finish_allowed"])

    def test_terminal_reason_required(self):
        self.ledger["tasks"] = [self.task("a", "blocked")]
        with self.assertRaises(ValueError):
            self.check_at(60)

    def test_cycle_rejected(self):
        self.ledger["tasks"] = [self.task("a", depends_on=["b"]), self.task("b", depends_on=["a"])]
        with self.assertRaises(ValueError):
            self.check_at(60)

    def test_screen_cap(self):
        self.ledger["new_paired_screens_started"] = 24
        self.ledger["tasks"] = [self.task("a", paired_screen=True), self.task("b", estimated_gpu_min=0)]
        self.assertEqual(self.check_at(60)["ready"], ["b"])


if __name__ == "__main__":
    unittest.main()
