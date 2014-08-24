# Python imports
import unittest
import datetime
import random

# Project imports
import posix_ipc
import base as tests_base

class TestSemaphores(tests_base.Base):
    def xrange(self, stop):
        """Return a range or xrange (if available) from 0 to stop.

        This is a hack to deal with Python 2/3 version straddling.
        """
        try:
            f = xrange
        except NameError:
            f = range

        return f(stop)


    def setUp(self):
        self.sem = posix_ipc.Semaphore(None, posix_ipc.O_CREX,
                                       initial_value=1)

    def tearDown(self):
        if self.sem:
            self.sem.unlink()

    def test_no_flags(self):
        """tests that opening a semaphore with no flags opens the existing
        semaphore and doesn't create a new semaphore"""
        sem_copy = posix_ipc.Semaphore(self.sem.name)
        self.assertEqual(self.sem.name, sem_copy.name)

    def test_o_creat_existing(self):
        """tests posix_ipc.O_CREAT to open an existing semaphore without
        O_EXCL"""
        sem_copy = posix_ipc.Semaphore(self.sem.name, posix_ipc.O_CREAT)

        self.assertEqual(self.sem.name, sem_copy.name)

    def test_o_creat_new(self):
        """tests posix_ipc.O_CREAT to create a new semaphore without O_EXCL"""
        # I can't pass None for the name unless I also pass O_EXCL.
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        name = '/' + ''.join(random.sample(alphabet, random.randint(3, 12)))

        name_is_available = False
        while not name_is_available:
            try:
                sem = posix_ipc.Semaphore(name)
                sem.close()
            except posix_ipc.ExistentialError:
                name_is_available = True
            else:
                name = '/' + ''.join(random.sample(alphabet, random.randint(3, 12)))

        sem = posix_ipc.Semaphore(name, posix_ipc.O_CREAT)

        self.assertIsNotNone(sem)

        sem.unlink()

    def test_o_excl(self):
        """tests O_CREAT | O_EXCL prevents opening an existing semaphore"""
        self.assertRaises(posix_ipc.ExistentialError, posix_ipc.Semaphore,
                          self.sem.name, posix_ipc.O_CREAT | posix_ipc.O_EXCL)

    def test_o_crex(self):
        """tests O_CREX prevents opening an existing semaphore"""
        self.assertRaises(posix_ipc.ExistentialError, posix_ipc.Semaphore,
                          self.sem.name, posix_ipc.O_CREX)

    def test_randomly_generated_name(self):
        """tests that the randomly-generated name works"""
        # This is tested implicitly elsewhere but I want to test it explicitly
        sem = posix_ipc.Semaphore(None, posix_ipc.O_CREX)
        self.assertIsNotNone(sem.name)

        self.assertEqual(sem.name[0], '/')
        self.assertGreaterEqual(len(sem.name), 2)
        sem.unlink()

    # don't bother testing mode, it's ignored by the OS?

    def test_default_initial_value(self):
        """tests that the initial value is 0 by default"""
        if posix_ipc.SEMAPHORE_VALUE_SUPPORTED:
            sem = posix_ipc.Semaphore(None, posix_ipc.O_CREX)
            self.assertEqual(sem.value, 0)
            sem.unlink()

    def test_zero_initial_value(self):
        """tests that the initial value is 0 when assigned"""
        if posix_ipc.SEMAPHORE_VALUE_SUPPORTED:
            sem = posix_ipc.Semaphore(None, posix_ipc.O_CREX, initial_value=0)
            self.assertEqual(sem.value, 0)
            sem.unlink()

    def test_nonzero_initial_value(self):
        """tests that the initial value is non-zero when assigned"""
        if posix_ipc.SEMAPHORE_VALUE_SUPPORTED:
            sem = posix_ipc.Semaphore(None, posix_ipc.O_CREX, initial_value=42)
            self.assertEqual(sem.value, 42)
            sem.unlink()


    # test sacquisition
    def test_simple_acquisition(self):
        """tests that acquisition works"""
        # I should be able to acquire this semaphore, but if I can't I don't
        # want to hang the test. Acquiring with timeout=0 will raise a BusyError
        # if the semaphore can't be acquired. That works even when
        # SEMAPHORE_TIMEOUT_SUPPORTED is False.
        self.sem.acquire(0)

    # test acquisition failures
    # def test_acquisition_no_timeout(self):
    # This is hard to test since it should wait infinitely. Probably the way
    # to do it is to spawn another process that holds the semaphore for
    # maybe 10 seconds and have this process wait on it. That's complicated
    # and not a really great test.

    def test_acquisition_zero_timeout(self):
        """tests that acquisition w/timeout=0 implements non-blocking
        behavior"""
        # Should not raise an error
        self.sem.acquire(0)

        # I would prefer this syntax, but it doesn't work with Python < 2.7.
        # with self.assertRaises(posix_ipc.BusyError):
        #     self.sem.acquire(0)
        self.failUnlessRaises(posix_ipc.BusyError, self.sem.acquire, 0)


    def test_acquisition_nonzero_int_timeout(self):
        """tests that acquisition w/timeout=an int is reasonably accurate"""
        if posix_ipc.SEMAPHORE_TIMEOUT_SUPPORTED:
            # Should not raise an error
            self.sem.acquire(0)

            # This should raise a busy error
            wait_time = 1
            start = datetime.datetime.now()
            # I would prefer this syntax, but it doesn't work with Python < 2.7.
            # with self.assertRaises(posix_ipc.BusyError):
            #     self.sem.acquire(wait_time)
            self.failUnlessRaises(posix_ipc.BusyError, self.sem.acquire,
                                  wait_time)
            end = datetime.datetime.now()
            actual_delta = end - start
            expected_delta = datetime.timedelta(seconds=wait_time)

            delta = actual_delta - expected_delta

            self.assertEqual(delta.days, 0)
            self.assertEqual(delta.seconds, 0)
            # I don't want to test microseconds because that granularity
            # isn't under the control of this module.
        # else:
            # Can't test this!

    def test_acquisition_nonzero_float_timeout(self):
        """tests that acquisition w/timeout=a float is reasonably accurate"""
        if posix_ipc.SEMAPHORE_TIMEOUT_SUPPORTED:
            # Should not raise an error
            self.sem.acquire(0)

            # This should raise a busy error
            wait_time = 1.5
            start = datetime.datetime.now()
            # I would prefer this syntax, but it doesn't work with Python < 2.7.
            # with self.assertRaises(posix_ipc.BusyError):
            #     self.sem.acquire(wait_time)
            self.failUnlessRaises(posix_ipc.BusyError, self.sem.acquire,
                                  wait_time)
            end = datetime.datetime.now()
            actual_delta = end - start
            expected_delta = datetime.timedelta(seconds=wait_time)

            delta = actual_delta - expected_delta

            self.assertEqual(delta.days, 0)
            self.assertEqual(delta.seconds, 0)
            # I don't want to test microseconds because that granularity
            # isn't under the control of this module.
        # else:
            # Can't test this!

    def test_release(self):
        """tests that release works"""
        # Not only does it work, I can do it as many times as I want! It's
        # interesting to try to do it the max number of times, but it takes
        # quite some time so I'll stick to a lower (but still very large)
        # number of releases.
        n_releases = min(1000000, posix_ipc.SEMAPHORE_VALUE_MAX - 1)
        for i in range(n_releases):
            self.sem.release()

    def test_context_manager(self):
        """tests that context manager acquire/release works"""
        with self.sem as sem:
            if posix_ipc.SEMAPHORE_VALUE_SUPPORTED:
                self.assertEqual(sem.value, 0)
            # I would prefer this syntax, but it doesn't work with Python < 2.7.
            # with self.assertRaises(posix_ipc.BusyError):
            #     sem.acquire(0)
            self.failUnlessRaises(posix_ipc.BusyError, sem.acquire, 0)

        if posix_ipc.SEMAPHORE_VALUE_SUPPORTED:
            self.assertEqual(sem.value, 1)

        # Should not raise an error.
        sem.acquire(0)

    def test_close_and_unlink(self):
        """tests that sem.close() and sem.unlink() works"""
        # sem.close() is hard to test since subsequent use of the semaphore
        # after sem.close() is undefined. All I can think of to do is call it
        # and note that it does not fail. Also, it allows sem.unlink() to
        # tell the OS to delete the semaphore entirely, so it makes sense
        # to test them together,
        #self.sem.close()

        self.sem.unlink()
        self.sem.close()
        self.assertRaises(posix_ipc.ExistentialError, posix_ipc.Semaphore,
                          self.sem.name)

        # Wipe this out so that self.tearDown() doesn't crash.
        self.sem = None

if __name__ == '__main__':
    unittest.main()
