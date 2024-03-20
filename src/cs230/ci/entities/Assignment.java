package cs230.ci.entities;

import java.util.Date;

import cs230.ci.AssignmentException;

/**
 * A mapping of a user to a particular job assignment.
 * 
 * @author Peter Ohmann
 */
public class Assignment {
	private User user;
	private String jobDescription;
	private Date dueDate;
	
	/**
	 * Create a job assignment with full details.
	 * 
	 * @param user the user to assign
	 * @param jobDescription a brief description of the job
	 * @param dueDate the initial due date for the assignment
	 */
	public Assignment(User user, String jobDescription, Date dueDate) {
		super();
		this.user = user;
		this.jobDescription = jobDescription;
		this.dueDate = dueDate;
	}

	/**
	 * Get the current assigned user.
	 * 
	 * @return the user assigned to this job
	 */
	public User getUser() {
		return user;
	}

	/**
	 * Assign a different user to the job.  Jobs cannot
	 * be unassigned, so null user is not valid.
	 * 
	 * @param user the new user to assign; cannot be null
	 * @throws AssignmentException if the provided user is null
	 */
	public void setUser(User user) throws AssignmentException {
		if (user == null)
			throw new AssignmentException("Invalid null assignment for job");
		this.user = user;
	}

	/**
	 * Get the current detailed job description.
	 * 
	 * @return the job description
	 */
	public String getJobDescription() {
		return jobDescription;
	}

	/**
	 * Update the job description.
	 * 
	 * @param jobDescription the new updated job description
	 */
	public void setJobDescription(String jobDescription) {
		this.jobDescription = jobDescription;
	}

	/**
	 * Get the current due date.
	 * 
	 * @return the due date
	 */
	public Date getDueDate() {
		return dueDate;
	}

	/**
	 * Update the due date.  All jobs must have a due date,
	 * so null is not a valid due date.
	 * 
	 * @param dueDate the new due date; cannot be null
	 * @throws AssignmentException if the provided date is null
	 * 
	 */
	public void setDueDate(Date dueDate) throws AssignmentException {
		if (dueDate == null)
			throw new AssignmentException("Due date required");
		this.dueDate = dueDate;
	}
	
	
}
