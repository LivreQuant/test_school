import random
from typing import Iterable, Optional, List
import pandas as pd
from .params import _PCTMAX_BIDDING_REMAIN_POINTS


class Student:
    _NEXT_AVAILABLE_ID = 1

    def __init__(self, points: int):
        self._id = Student._assign_id()
        self._points = points
        self._choices: Optional[dict] = None  # dictionary of subjects and bidding points
        self._enrolled: Optional[List[str]] = []  # final list of enrolled courses (CHANGE TO EMPTY LIST)

    def __repr__(self):
        if self:
            top_bids = sorted([(k, v) for k, v in self._choices.items()], key=lambda x: x[1], reverse=True)
            top_three_ = ', '.join(f"{subj}={pts}" for subj, pts in top_bids[:3])
            str_ = f'{self.__class__.__name__} (id={self._id}, Top 3 Picks: ({top_three_}))'
        else:
            str_ = f'{self.__class__.__name__} (id={self._id}, points={self._points})'
        return str_

    def __bool__(self):
        return False if self._choices is None else True

    def bid(self, courses: Iterable[str]):
        if self._choices is None:
            shuffled = [subj for subj in courses]
            self._choices = {s: 0 for s in shuffled}
            random.shuffle(shuffled)
            remain_points = self._points
            for subj in shuffled:
                bid_points = random.randint(0, int(remain_points * _PCTMAX_BIDDING_REMAIN_POINTS))
                self._choices[subj] = bid_points
                remain_points -= bid_points
            # assign any remaining points to the highest bid
            top_subj = sorted([(k, v) for k, v in self._choices.items()], key=lambda x: x[1], reverse=True)[0][0]
            self._choices[top_subj] = self._choices[top_subj] + remain_points
        else:
            raise RuntimeError(f'Student (id={self._id}) already used all bidding points!')

    def enroll(self, courses: Iterable[str]):
        self._enrolled = courses

    @property
    def id(self):
        return self._id

    @property
    def bidding(self):
        return self._choices

    @property
    def enrolled(self):
        return self._enrolled

    @classmethod
    def _assign_id(cls):
        id_ = cls._NEXT_AVAILABLE_ID
        cls._NEXT_AVAILABLE_ID += 1
        return id_


class StudentBody:
    def __init__(self, *, n_students: int, bidding_points: int):
        students = [Student(bidding_points) for _ in range(n_students)]
        self._students = {stu.id: stu for stu in students}
        self._courses = None

    def __iter__(self):
        return iter(self._students.values())

    def __len__(self):
        return len(self._students)

    def __getitem__(self, student_id):
        return self._students[student_id]

    def __bool__(self):
        bools = [bool(stu) for stu in self]
        return all(bools)

    def __repr__(self):
        return f'{self.__class__.__name__}(n={len(self._students)})'

    @property
    def students(self):
        return self._students

    def request_bidding(self, available_courses: Iterable[str]):
        self._courses = available_courses
        for _, student in self._students.items():
            student.bid(available_courses)

    def summary_bidding(self):
        df = pd.DataFrame({stu.id: stu.bidding for stu in self}).T if self else pd.DataFrame()
        return df

    def enroll_student(self, student_id: int, courses: Iterable[str]):
        student = self._students[student_id]
        student.enroll(courses)
