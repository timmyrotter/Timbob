package cs230.ci.entities;

import java.util.Date;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import cs230.ci.AssignmentException;

public class AssignmentTest {
	private Assignment theAssignment;
	private User user1;
	private User user2;

	@SuppressWarnings("deprecation")
	@Before
	public void setUp() throws Exception {
		user1 = new User("pohmann", "pass", "Peter", "Ohmann", 100);
		user2 = new User("irahal", "secure", "Imad", "Rahal", 102);
		theAssignment = new Assignment(user1, "Grade homework", new Date(2024, 01, 20));
	}

	@After
	public void tearDown() throws Exception {
		// nothing to do!
	}

	@Test
	public void testSetUser() {
		// ensure that we can't set null as a user
		try {
			theAssignment.setUser(null);
			throw new Error("Null user is possible!");
		}
		catch (AssignmentException e) {
			// this is expected!
		}

		// but that we can set a real User object
		try {
			theAssignment.setUser(user2);
		}
		catch (AssignmentException e) {
			throw new Error("Can't set a regular user!");
		}
	}

	@SuppressWarnings("deprecation")
	@Test
	public void testSetDueDate() {
		// ensure that we can't set null as a due date
		try {
			theAssignment.setDueDate(null);
			throw new Error("Null due date is possible!");
		}
		catch (AssignmentException e) {
			// this is expected!
		}

		// but that we can set a real Date object
		try {
			theAssignment.setDueDate(new Date(2025, 01, 01));
		}
		catch (AssignmentException e) {
			throw new Error("Can't set a regular Date object!");
		}
	}

}
