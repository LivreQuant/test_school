from source import SchoolTerm

if __name__ == '__main__':
    # setup school term
    st = SchoolTerm(n_students=250,
                    bidding_points=50,
                    n_courses=5)

    # test __bool__
    print("COURSES FILLED: {0}".format(bool(st)))

    # enroll students with optimization
    st.enroll_students()

    # compute final course enrollment
    st.final_placement()

    # test __bool__
    print("COURSES FILLED: {0}".format(bool(st)))

    # test __repr__
    print(st)

    # evaluate courses
    print("ENROLLMENT: {0}".format(st.course_enrollment))
