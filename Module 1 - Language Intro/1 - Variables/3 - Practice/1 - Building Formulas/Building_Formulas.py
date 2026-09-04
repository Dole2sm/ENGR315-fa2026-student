# in this problem, you will practice building the rate function shown in the notes
# by splitting each calculation up into separate variables, using the
# previous variable in the subsequent calculation.
# use the print function under the variables to make sure they're right

# Here are the variables to use: DO NOT CHANGE THESE
principal = 1000  # initial amount to be deposited
rate = 1  # interest rate applied to deposit (will be divided by 100)
n = 10  # number of years to compound deposit

# your equation should be functionally the same as this:
# final = principal * ((1 + (rate / 100)) ** n)


# Step One: Divide Rate by 100
step_one = rate / 100

# Step Two: Add One to the step_one, then raise it the nth power
step_two = (1 + step_one) ** n

# Step Three: Multiply the step_two by the Principal
step_three = principal*step_two

# step_three should be around 1105, use a print statement to check:
print(step_three)

# ----------------------------------------------------------------------------------------------------------------------

# Now, build the same formula all in one line.

# Here are the variables: DO NOT CHANGE
R = 70    # Rate
N = 6     # n - exponent
K = 2500  # Principal

# write the equation here, using the variable names above:
growth = K * ((1 + (R / 100)) ** N)

# Use a print statement to check your work, growth should be around 60,343:
print(growth)