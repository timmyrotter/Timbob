package cs230.ci.entities;

/**
 * The user class represents a user of our system.
 * 
 * @author Peter Ohmann
 */
public class User {
	private String username;
	private String password;
	private String firstName;
	private String lastName;
	private int age;
	
	/**
	 * Construct a User given complete information.
	 * 
	 * @param username the (unique) username for this user
	 * @param password their password
	 * @param firstName their first name
	 * @param lastName their last (family) name
	 * @param age their age, in years
	 */
	public User(String username, String password, String firstName, String lastName, int age) {
		this.username = username;
		this.password = password;
		this.firstName = firstName;
		this.lastName = lastName;
		this.age = age;
	}

	/**
	 * Get the user's password.
	 * 
	 * @return the password
	 */
	public String getPassword() {
		return password;
	}

	/**
	 * Update the user's password.
	 * 
	 * @param password the password to set
	 */
	public void setPassword(String password) {
		this.password = password;
	}

	/**
	 * Get the user's first name.
	 * 
	 * @return the user's first name
	 */
	public String getFirstName() {
		return firstName;
	}

	/**
	 * Update the user's first name.
	 * @param firstName the firstName to set
	 */
	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}

	/**
	 * Get the user's last (family) name.
	 * 
	 * @return the the user's last name
	 */
	public String getLastName() {
		return lastName;
	}

	/**
	 * Update the user's last (family) name.
	 * 
	 * @param lastName the new last name to set
	 */
	public void setLastName(String lastName) {
		this.lastName = lastName;
	}

	/**
	 * Get the user's unique username.
	 * 
	 * @return the username for this user
	 */
	public String getUsername() {
		return username;
	}

	/**
	 * Get the user's current age in years.
	 * 
	 * @return the age in years
	 */
	public int getAge() {
		return age;
	}
	
	/**
	 * Get the user's full (first and last) name.
	 * 
	 * @return the user's full name
	 */
	public String getFullName() {
		// Wait...the order here doesn't seem quite right...
		// I think I found the bug!!!
		return this.getFirstName() + " " + this.getLastName();
	}
	
}
