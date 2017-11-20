import logging
from operator import attrgetter
from threading import RLock

logger = logging.getLogger('judge.bridge')


class JudgeList(object):
    def __init__(self):
        self.queue = []
        self.judges = set()
        self.submission_map = {}
        self.lock = RLock()

    def _handle_free_judge(self, judge):
        with self.lock:
            for i, elem in enumerate(self.queue):
                id, problem, language, source = elem
                if judge.can_judge(problem, language):
                    self.submission_map[id] = judge
                    logger.info('Dispatched queued submission %d: %s', id, judge.name)
                    try:
                        judge.submit(id, problem, language, source)
                    except Exception:
                        logger.exception('Failed to dispatch %d (%s, %s) to %s', id, problem, language, judge.name)
                        self.judges.remove(judge)
                        return
                    del self.queue[i]
                    break

    def register(self, judge):
        with self.lock:
            self.judges.add(judge)
            self._handle_free_judge(judge)

    def update_problems(self, judge):
        with self.lock:
            self._handle_free_judge(judge)

    def remove(self, judge):
        with self.lock:
            sub = judge.get_current_submission()
            if sub is not None:
                try:
                    del self.submission_map[sub]
                except KeyError:
                    pass
            self.judges.discard(judge)

    def __iter__(self):
        return iter(self.judges)

    def on_judge_free(self, judge, submission):
        with self.lock:
            logger.info('Judge available after grading %d: %s', submission, judge.name)
            del self.submission_map[submission]
            self._handle_free_judge(judge)

    def abort(self, submission):
        with self.lock:
            logger.info('Abort request: %d', submission)
            self.submission_map[submission].abort()

    def judge(self, id, problem, language, source):
        with self.lock:
            if id in self.submission_map:
                logger.warning('Already judging? %d', id)
                return

            candidates = [judge for judge in self.judges if not judge.working and judge.can_judge(problem, language)]
            logger.info('Free judges: %d', len(candidates))
            if candidates:
                judge = min(candidates, key=attrgetter('load'))
                logger.info('Dispatched submission %d to: %s', id, judge.name)
                self.submission_map[id] = judge
                try:
                    judge.submit(id, problem, language, source)
                except Exception:
                    logger.exception('Failed to dispatch %d (%s, %s) to %s', id, problem, language, judge.name)
                    self.judges.discard(judge)
                    return self.judge(id, problem, language, source)
            else:
                self.queue.append((id, problem, language, source))
                logger.info('Queued submission: %d', id)
