package cs230.ci.entities;

import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

public class UserTest {
	User testUser;

	@Before
	public void setUp() throws Exception {
		testUser = new User("pohmann", "pass", "Peter", "Ohmann", 100);
	}

	@After
	public void tearDown() throws Exception {
		// no DB, so nothing to do!
	}

	@Test
	public void testSetPassword() {
		// check original password
		Assert.assertEquals("pass", testUser.getPassword());
		// change the password
		testUser.setPassword("secure");
		// check if the password is updated
		Assert.assertEquals("secure", testUser.getPassword());
	}

	@Test
	public void testSetFirstName() {
		// check original first name
		Assert.assertEquals("Peter", testUser.getFirstName());
		// change the first name
		testUser.setFirstName("Pete");
		// check if the name is updated
		Assert.assertEquals("Pete", testUser.getFirstName());
	}

	@Test
	public void testGetFullName() {
		Assert.assertEquals("Peter Ohmann", testUser.getFullName());
	}

}
