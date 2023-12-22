import random
from .student import StudentBody, Student
from .params import (NUMBER_OF_STUDENTS,
                     POINTS_PER_STUDENT,
                     NR_COURSES_OFFERED,
                     POSSIBLE_COURSES,
                     MAX_ENROLLMENT_PER_CLASS,
                     MIN_ENROLLMENT_PER_CLASS,
                     MAX_CLASSES_PER_STUDENT)

import numpy as np
from mip import Model, xsum, maximize, BINARY, OptimizationStatus

class SchoolTerm:
    def __init__(self,
                 n_students: int = NUMBER_OF_STUDENTS,
                 bidding_points: int = POINTS_PER_STUDENT,
                 n_courses: int = NR_COURSES_OFFERED
                 ):

        self._student_body = StudentBody(n_students=n_students, bidding_points=bidding_points)
        self._offered_courses = self._available_courses(n_courses)

        # TODO: Implement courses vs students (possibly used in final_placement() method below)
        self._courses_vs_students = {course: [] for course in self._offered_courses}

        # INITIALIZE: student will now bid for the available courses
        self._student_body.request_bidding(self._offered_courses)

    # TODO: Implement logic
    def __bool__(self):
        # True if courses are filled
        bools = [len(v) for v in self._courses_vs_students.values()]
        return all(bools)

    # TODO: Implement __repr__
    def __repr__(self):
        return f'{self.__class__.__name__}(n_students={len(self._student_body)}, n_courses={len(self._offered_courses)})'

    @property
    def course_enrollment(self):
        return self._courses_vs_students

    # TODO: Implement student enrollment logic; ** remember method: StudentBody.enroll_student()
    def enroll_students(self):
        """
        Optimize the students per class based using the Knapsack problem.

            VARIABLE:       x_{i,j} \in {0, 1} for Student {i} to attend Course {j}


            Maximize        sum_{i in students, j in courses} ( bid_{i,j} * x_{i,j} )
            w.r.t. x

            such that
                            // student constraints
                            sum_{i in students} x_{i,J} <= MAX_ENROLLMENT_PER_CLASS | for all Courses J
                            sum_{i in students} x_{i,J} >= MIN_ENROLLMENT_PER_CLASS | for all Courses J

                            // course constraints
                            sum_{j in courses} x_{I,j} <= len(self._offered_courses) | for all Students I
                            sum_{j in courses} x_{I,j} >= 1 | for all Students I

                            x_{I,J} \in {0,1} | for all Students I and Courses J

        :return:
            Enroll students in courses which maximizes happiness relative to bids and satisfies any
            course and student enrollment constraints.
        """

        # get student bids
        df = self._student_body.summary_bidding()

        # convert into a matrix
        A = df.to_numpy()

        # unravel the matrix to prevent doing Hadamard products
        p = A.ravel() # student [1, 2, 3, ... ]

        # setup optimization statement
        print("setting up the optimization statement ...")
        m = Model("knapsack")
        I = range(len(p))

        # students final enrollments
        x = [m.add_var(var_type=BINARY) for i in I]

        # objective statement
        m.objective = maximize(xsum(p[i] * x[i] for i in I))

        # get dimensions
        num_students, num_courses = A.shape

        # setup student constraints
        print("appending student constraints ...")
        for idx in range(num_students):
            w = np.zeros_like(A)
            w[idx,] = 1
            w = w.ravel()

            # [[0, 0, 0, 0, 0],
            #  [0, 0, 0, 0, 0],
            #  ...............
            #  [1, 1, 1, 1, 1], <- Student IDX
            #  ...............
            #  [0, 0, 0, 0, 0],
            #  [0, 0, 0, 0, 0]]

            # bound number of classes by limits
            m += xsum(w[i] * x[i] for i in I) <= min(MAX_CLASSES_PER_STUDENT, num_courses)
            m += xsum(w[i] * x[i] for i in I) >= 1

        # setup course constraints
        print("appending course constraints ...")
        for idx in range(num_courses):
            w = np.zeros_like(A)
            w[:, [idx]] = 1
            w = w.ravel()

            #            | <- Course IDX
            # [[0, 0, 0, 1, 0],
            #  [0, 0, 0, 1, 0],
            #  ...............
            #  [0, 0, 0, 1, 0],
            #  ...............
            #  [0, 0, 0, 1, 0],
            #  [0, 0, 0, 1, 0]]

            # bounder number of students by limits
            m += xsum(w[i] * x[i] for i in I) <= MAX_ENROLLMENT_PER_CLASS
            m += xsum(w[i] * x[i] for i in I) >= MIN_ENROLLMENT_PER_CLASS

        m.verbose = 0
        status = m.optimize()

        if status == OptimizationStatus.OPTIMAL:
            print('Objective Function: {} '.format(m.objective_value))
        elif status == OptimizationStatus.FEASIBLE:
            print('Objective Function: {}, Best Possible: {}'.format(m.objective_value, m.objective_bound))
        elif status == OptimizationStatus.NO_SOLUTION_FOUND:
            raise Exception('No feasible solution found, lower bound is: {}'.format(m.objective_bound))
        elif status == OptimizationStatus.INFEASIBLE:
            raise Exception('No feasible solution found')
        else:
            raise Exception('Unknown solution status: {}'.format(status))

        if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
            print('***************')
            print('Solution Found!')
            print('***************')

            selected = [i for i in I if x[i].x >= 0.99]

            s = np.zeros_like(p)
            for idx in selected:
                s[idx] = 1
            S = s.reshape(num_students, num_courses)

            student_ids = df.index
            for idx,std_id in enumerate(student_ids):
                courses = [self._offered_courses[x] for x in np.where(S[idx,] == 1)[0]]
                self._student_body.enroll_student(student_id=std_id, courses=courses)

    # TODO: Some object showing all enrollments for all students
    def final_placement(self):
        self._courses_vs_students = {course: self.__get_enrollment(course) for course in self._offered_courses}

    # TODO: Implement method to fetch student by id
    def fetch_students(self, std_id: int) -> Student:
        try:
            return self._student_body[std_id]
        except KeyError:
            raise Exception("KeyError: std_id = {0} NOT FOUND".format(std_id))

    @staticmethod
    def _available_courses(n_courses: int):
        codes = list(POSSIBLE_COURSES.keys())
        random.shuffle(codes)
        courses = codes[:n_courses]
        return courses

    def __get_enrollment(self, course: str):
        return [self.fetch_students(x) for x in self._student_body.students if
                (course in self.fetch_students(x).enrolled)]