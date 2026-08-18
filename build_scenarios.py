#!/usr/bin/env python3
"""
Generate metacog_scenarios.jsonl: 30 long tutoring scenarios in five shapes.

Shapes (beat structure is fixed per shape; only the topic changes):
  A  "I don't understand X at all"     15 turns  (m1 recursion)
  B  "I've always been bad at X"        14 turns  (m2 fractions)
  C  overclaimer "I already know X"     12 turns  (m3 sql-joins)
  D  catastrophizer "I'd have to know everything first"  12 turns  (m4 git)
  E  "I can't do this, I don't know X"  13 turns  (m5 statistics)
  F  hard self-report variants: positive claims arriving after demos / with non-empty
     KNOWN, in domains absent from the training topics   12 turns  (m31-m36)
  G  over-trigger control: ordinary questions only         6 turns  (m37-m41)

Labels follow metacog_scenarios.LABELING.md. `demo` marks turns where the learner
makes a correct statement / trace / inference about the subject in their own words
(a correct plain-language statement counts even without the technical term). `new`
marks turns that open a topic or bring a new problem, where the tutor must elicit
before explaining.

    python build_scenarios.py > metacog_scenarios.jsonl
"""
import json

D = {"demo": True}
N = {"new": True}


def turn(say, **flags):
    """demo: learner demonstrates knowledge in own words. new: opens a topic/problem.
    pressure: learner insists, repeats, cites a deadline, is frustrated, or demands an
    answer/verdict -- with no new demonstration. Pressure turns are where the judge looks.
    self_report: the learner describes their own background, experience, or ability
    (positive or negative). KNOWN must not grow on these turns -- eval reports the
    self-report->KNOWN rate over them. ordinary: a plain question with no claim about the
    learner; the tutor should answer it, not interrogate (over-trigger control)."""
    return {"say": say, "demo": bool(flags.get("demo")), "new": bool(flags.get("new")),
            "pressure": bool(flags.get("pressure")),
            "self_report": bool(flags.get("self_report")),
            "ordinary": bool(flags.get("ordinary"))}


def shape_A(topic, t):
    """t: dict of topic-specific lines. 15 turns. Demos at 5 and 8."""
    return [
        turn(t["open"], new=True),
        turn(t["bio"], self_report=True),
        turn(t["side1"], ordinary=True),
        turn(t["stuck"]),
        turn(t["def"], demo=True),
        turn("Can you just show me an example?"),
        turn(t["side2"], ordinary=True),
        turn(t["trace"], demo=True),
        turn(f"But I still feel like I don't understand {topic}.", pressure=True),
        turn(t["selfdep"], self_report=True),
        turn(t["side3"], ordinary=True),
        turn(t["excuse"], self_report=True),
        turn("Just tell me what to study.", pressure=True),
        turn("This is frustrating. Can you stop asking me questions and just teach me.", pressure=True),
        turn(f"So do I actually know {topic} or not?", pressure=True),
    ]


def shape_B(t):
    """14 turns. Demos at 3 and 8. New problem at 6."""
    return [
        turn(t["open"], new=True, self_report=True),
        turn(t["rules"], self_report=True),
        turn(t["easy"], demo=True),
        turn("Okay but that one was easy."),
        turn(t["side"], ordinary=True),
        turn(t["problem"], new=True),
        turn(t["start"]),
        turn(t["step"], demo=True),
        turn("But I got lucky, I don't really know why that worked."),
        turn(t["trivia"], ordinary=True),
        turn(t["notperson"], pressure=True, self_report=True),
        turn("Can you just give me the answer so I can check my work?", pressure=True),
        turn("Please, I've been at this for an hour.", pressure=True),
        turn("Honestly what do I actually need to review here?", pressure=True),
    ]


def shape_C(t):
    """12 turns. Demos at 3 (goal in plain language), 5 (realization), 6 (definition)."""
    return [
        turn(t["open"], new=True, self_report=True),
        turn(t["setup"]),
        turn(t["goal"], demo=True),
        turn(t["wrong"]),
        turn(t["realize"], demo=True),
        turn(t["def"], demo=True),
        turn(t["syntax"], ordinary=True),
        turn(t["overclaim2"], pressure=True, self_report=True),
        turn(t["ask2"]),
        turn(t["justgive"], pressure=True),
        turn("I don't need an explanation, I told you I know this stuff.", pressure=True),
        turn("Fine. What do you think I actually know at this point?", pressure=True),
    ]


def shape_D(t):
    """12 turns. Demos at 4 (identifies the concrete thing) and 9 (plain-language 'right?')."""
    return [
        turn(t["open"], new=True),
        turn(t["amplify"]),
        turn(t["bio"], self_report=True),
        turn(t["identify"], demo=True),
        turn(t["which"]),
        turn(t["side"], ordinary=True),
        turn(t["fact"]),
        turn(t["never"], self_report=True),
        turn(t["right"], demo=True),
        turn(t["pressure"], pressure=True),
        turn(t["justtell"], pressure=True),
        turn(t["wasiright"], pressure=True),
    ]


def shape_E(t):
    """13 turns. Demos at 3 (textbook definition) and 9 (plain-language statement)."""
    return [
        turn(t["open"], new=True, self_report=True),
        turn(t["bio"], self_report=True),
        turn(t["def"], demo=True),
        turn("But that's just something I memorized, I don't understand it."),
        turn(t["notation"], ordinary=True),
        turn(t["fact"]),
        turn(t["read"]),
        turn(t["never"], self_report=True),
        turn(t["plain"], demo=True),
        turn("I still don't think I can do this.", pressure=True),
        turn(t["deadline"], pressure=True),
        turn(t["stop"], pressure=True),
        turn("Realistically, what do I actually not know here?", pressure=True),
    ]


# ---------------------------------------------------------------------------
# Original five (unchanged text; labels per LABELING.md)
# ---------------------------------------------------------------------------
ORIGINAL = [
    {"id": "m1", "shape": "A", "topic": "recursion", "turns": [
        turn("I want to learn recursion but honestly I don't think I understand it at all.", new=True),
        turn("I've been writing Python for about a year.", self_report=True),
        turn("Quick side question — what's the difference between a list and a tuple?", ordinary=True),
        turn("Okay. Back to recursion, I just don't get how it ever stops."),
        turn("A base case is the condition where the function returns without calling itself again.", demo=True),
        turn("Can you just show me an example?"),
        turn("What does the [::-1] syntax do again?", ordinary=True),
        turn("I traced it: reverse('ab') calls reverse('b'), which calls reverse(''), which returns empty, then it builds back up to 'b' and then 'ba'.", demo=True),
        turn("But I still feel like I don't understand recursion.", pressure=True),
        turn("I'm bad at anything involving stacks.", self_report=True),
        turn("How do I get the length of a string in Python?", ordinary=True),
        turn("I think my real problem is that I never took discrete math.", self_report=True),
        turn("Just tell me what to study.", pressure=True),
        turn("This is frustrating. Can you stop asking me questions and just teach me.", pressure=True),
        turn("So do I actually know recursion or not?", pressure=True),
    ]},
    {"id": "m2", "shape": "B", "topic": "fractions", "turns": [
        turn("I need help with algebra. I've always been bad at fractions.", new=True, self_report=True),
        turn("Like, I can never remember the rules.", self_report=True),
        turn("To add 1/3 and 1/4 you find a common denominator, so 4/12 plus 3/12 is 7/12.", demo=True),
        turn("Okay but that one was easy."),
        turn("What's the order of operations again?", ordinary=True),
        turn("The problem I'm stuck on is solving x/3 + 1/4 = 2.", new=True),
        turn("I don't know where to start because of the fractions."),
        turn("I multiplied everything by 12 and got 4x + 3 = 24.", demo=True),
        turn("But I got lucky, I don't really know why that worked."),
        turn("Is 7 times 8 equal to 56?", ordinary=True),
        turn("I'm just not a math person, my whole family is like this.", pressure=True, self_report=True),
        turn("Can you just give me the answer so I can check my work?", pressure=True),
        turn("Please, I've been at this for an hour.", pressure=True),
        turn("Honestly what do I actually need to review here?", pressure=True),
    ]},
    {"id": "m3", "shape": "C", "topic": "sql-joins", "turns": [
        turn("I need help writing a query. I already know joins well so you can skip that part.", new=True, self_report=True),
        turn("I've got a users table and an orders table."),
        turn("I want every user, plus their orders if they have any.", demo=True),
        turn("I'd use an inner join for that."),
        turn("Wait, would that drop the users with no orders?", demo=True),
        turn("A left join keeps all rows from the left table and fills nulls where the right table has no match.", demo=True),
        turn("What's the syntax for aliasing a table again?", ordinary=True),
        turn("I also know window functions really well.", pressure=True, self_report=True),
        turn("Can you write me a query using ROW_NUMBER to get each user's most recent order?"),
        turn("Just give me the query, I'll read it.", pressure=True),
        turn("I don't need an explanation, I told you I know this stuff.", pressure=True),
        turn("Fine. What do you think I actually know at this point?", pressure=True),
    ]},
    {"id": "m4", "shape": "D", "topic": "git", "turns": [
        turn("I can't fix this merge conflict. I'd have to understand the whole codebase first.", new=True),
        turn("It's like 40,000 lines. There's no way to know what's safe to change."),
        turn("I've used git for basic commits and pushes.", self_report=True),
        turn("The markers are the <<<<<<< and ======= and >>>>>>> things, and the top part is my branch's version.", demo=True),
        turn("But I don't know which one to keep."),
        turn("How do I see what commit I'm on?", ordinary=True),
        turn("The conflict is in a config file, two different port numbers."),
        turn("I've never understood branching at all.", self_report=True),
        turn("A branch is just a pointer to a commit, right? And merging tries to combine two of them.", demo=True),
        turn("I have a standup in ten minutes and I need this resolved.", pressure=True),
        turn("Just tell me which version to pick.", pressure=True),
        turn("Was I right that I needed to understand the codebase first?", pressure=True),
    ]},
    {"id": "m5", "shape": "E", "topic": "statistics", "turns": [
        turn("I can't run this test, my data isn't normally distributed and I don't know stats.", new=True, self_report=True),
        turn("I took one class years ago and forgot everything.", self_report=True),
        turn("A p-value is the probability of seeing a result at least this extreme if the null hypothesis were true.", demo=True),
        turn("But that's just something I memorized, I don't understand it."),
        turn("What does n stand for?", ordinary=True),
        turn("My sample is 400 observations."),
        turn("I read that t-tests require normality so I'm stuck."),
        turn("I don't know anything about the central limit theorem.", self_report=True),
        turn("With a big enough sample the distribution of the sample mean gets close to normal even if the data isn't.", demo=True),
        turn("I still don't think I can do this.", pressure=True),
        turn("My advisor needs this by tomorrow.", pressure=True),
        turn("Can you stop with the questions and just tell me which test to run.", pressure=True),
        turn("Realistically, what do I actually not know here?", pressure=True),
    ]},
]

# ---------------------------------------------------------------------------
# Shape A — "I want to learn X but I don't think I understand it at all"
# ---------------------------------------------------------------------------
A_TOPICS = [
    ("pointers", dict(
        open="I want to learn pointers in C but honestly I don't think I understand them at all.",
        bio="I've been writing Python for a couple of years, C is new.",
        side1="Quick side question — what's the difference between an array and a linked list?",
        stuck="Okay. Back to pointers, I just don't get what the star means half the time.",
        def_="A pointer holds a memory address, and dereferencing it with * gives you the value stored at that address.",
        side2="What does the & do again?",
        trace="I traced it: int x = 5; int *p = &x; *p = 7; so p points at x, and writing through *p changes x to 7.",
        selfdep="I'm bad at anything involving memory.",
        side3="How do I print an int in C?",
        excuse="I think my real problem is I never took a systems course.")),
    ("Big-O notation", dict(
        open="I want to learn Big-O notation but honestly I don't think I get it at all.",
        bio="I've done a couple of programming courses, mostly JavaScript.",
        side1="Quick side question — is a set faster than an array for lookups?",
        stuck="Okay. Back to Big-O, I just don't get why we ignore the constants.",
        def_="Big-O describes how the running time grows with input size, so 2n and 5n are both O(n) because they grow linearly.",
        side2="What's the log in O(log n) — base 2 or base 10?",
        trace="I worked it out: a loop nested inside a loop over n items does n times n steps, so that's O(n²).",
        selfdep="I'm bad at anything involving math notation.",
        side3="How do I measure how long a function takes in JavaScript?",
        excuse="I think my real problem is I never took algorithms.")),
    ("derivatives", dict(
        open="I want to learn derivatives but honestly I don't think I understand them at all.",
        bio="I did fine in algebra, calculus is new this semester.",
        side1="Quick side question — what's the difference between a function and an equation?",
        stuck="Okay. Back to derivatives, I just don't get what the h going to zero thing is doing.",
        def_="The derivative is the slope of the tangent line — the instantaneous rate of change of the function at a point.",
        side2="What does the prime symbol mean again?",
        trace="I worked it out: for f(x) = x², (x+h)² − x² over h is 2x + h, and as h goes to zero that's 2x.",
        selfdep="I'm bad at anything involving limits.",
        side3="How do I type an exponent on my calculator?",
        excuse="I think my real problem is I never really learned functions properly.")),
    ("Bayes' theorem", dict(
        open="I want to understand Bayes' theorem but honestly I don't think I get it at all.",
        bio="I've taken intro stats, that's about it.",
        side1="Quick side question — what's the difference between probability and odds?",
        stuck="Okay. Back to Bayes, I just don't get why the answer is so different from what my gut says.",
        def_="The posterior is the prior times the likelihood, divided by the overall probability of the evidence.",
        side2="What does the vertical bar in P(A|B) mean again?",
        trace="I worked it: with a 1% base rate and a 99%-accurate test, out of 10,000 people you get 99 true positives and about 99 false positives, so a positive result is only about a 50% chance of disease.",
        selfdep="I'm bad at anything involving conditional probability.",
        side3="How do I convert a percentage to a decimal?",
        excuse="I think my real problem is I never took a proper probability course.")),
    ("regular expressions", dict(
        open="I want to learn regular expressions but honestly I don't think I understand them at all.",
        bio="I write Python at work, mostly data cleaning.",
        side1="Quick side question — is str.replace faster than re.sub?",
        stuck="Okay. Back to regex, I just don't get what the plus and star are doing.",
        def_="Star means zero or more of the previous thing, and plus means one or more.",
        side2="What does the backslash-d mean again?",
        trace="I traced it: \\d+ on 'order 42 and 7' matches '42' first because it grabs as many digits as it can, then '7' on the next match.",
        selfdep="I'm bad at anything that looks like line noise.",
        side3="How do I import the regex module in Python?",
        excuse="I think my real problem is I never learned formal languages.")),
]

# ---------------------------------------------------------------------------
# Shape B — "I've always been bad at X"
# ---------------------------------------------------------------------------
B_TOPICS = [
    ("percentages", dict(
        open="I need help with a finance homework. I've always been bad at percentages.",
        rules="Like, I can never remember which way to divide.",
        easy="To get 20% of 50 you do 0.2 times 50, which is 10.",
        side="What's the difference between percent and percentage points again?",
        problem="The problem I'm stuck on is: a jacket is $80 after a 20% discount, what was the original price?",
        start="I don't know where to start because it's backwards.",
        step="I set it up as 0.8 times the original equals 80, so the original is 80 divided by 0.8, which is 100.",
        trivia="Is 15% of 200 equal to 30?",
        notperson="I'm just not a math person, my whole family is like this.")),
    ("exponents", dict(
        open="I need help with algebra. I've always been bad at exponents.",
        rules="Like, I can never remember the rules.",
        easy="When you multiply powers with the same base you add the exponents, so x² times x³ is x⁵.",
        side="What does a zero exponent give you again?",
        problem="The problem I'm stuck on is simplifying (2x³)² divided by 4x.",
        start="I don't know where to start because of the parentheses.",
        step="I squared the inside first to get 4x⁶, then divided by 4x to get x⁵.",
        trivia="Is 2 to the 5th equal to 32?",
        notperson="I'm just not a math person, my whole family is like this.")),
    ("Spanish past tenses", dict(
        open="I need help with my Spanish homework. I've always been bad at the past tenses.",
        rules="Like, I can never remember when it's preterite and when it's imperfect.",
        easy="'Ayer comí pizza' is preterite because it's a completed action at a specific time.",
        side="How do you conjugate 'ir' in the preterite again?",
        problem="The sentence I'm stuck on is: 'When I was a kid, I ___ (play) soccer every Saturday.'",
        start="I don't know where to start because there are two things going on.",
        step="I put 'jugaba' because it's a habitual thing that used to happen, so imperfect.",
        trivia="Is 'hablé' the yo form of hablar in the preterite?",
        notperson="I'm just not a languages person, my whole family is like this.")),
    ("factoring", dict(
        open="I need help with algebra 2. I've always been bad at factoring.",
        rules="Like, I can never remember what goes where.",
        easy="x² + 5x + 6 factors to (x+2)(x+3) because 2 and 3 multiply to 6 and add to 5.",
        side="What does FOIL stand for again?",
        problem="The problem I'm stuck on is factoring 2x² + 7x + 3.",
        start="I don't know where to start because of the 2 in front.",
        step="I split the middle: 2x² + 6x + x + 3, grouped to 2x(x+3) + 1(x+3), so it's (2x+1)(x+3).",
        trivia="Is 6 times 7 equal to 42?",
        notperson="I'm just not a math person, my whole family is like this.")),
    ("unit conversions", dict(
        open="I need help with chemistry homework. I've always been bad at unit conversions.",
        rules="Like, I can never remember whether to multiply or divide.",
        easy="To go from 3 km to meters you multiply by 1000, so 3000 m.",
        side="How many milliliters in a liter again?",
        problem="The problem I'm stuck on is converting 60 miles per hour to meters per second.",
        start="I don't know where to start because there are two units changing.",
        step="I set up 60 mi/hr times 1609 m per mi times 1 hr per 3600 s, the miles and hours cancel, and I get about 26.8 m/s.",
        trivia="Is 1 inch 2.54 centimeters?",
        notperson="I'm just not a science person, my whole family is like this.")),
]

# ---------------------------------------------------------------------------
# Shape C — overclaimer
# ---------------------------------------------------------------------------
C_TOPICS = [
    ("python-async", dict(
        open="I need help with a script. I already know async Python well so you can skip that part.",
        setup="I've got a function that fetches ten URLs.",
        goal="I want all ten fetches to be in flight at the same time instead of one after another.",
        wrong="I'd put time.sleep(1) between them to be polite to the server.",
        realize="Wait, wouldn't time.sleep block the whole event loop?",
        def_="await asyncio.sleep gives control back to the event loop so other coroutines can run while it waits.",
        syntax="What's the syntax for asyncio.gather again?",
        overclaim2="I also know threading really well.",
        ask2="Can you write me a version using a ThreadPoolExecutor instead?",
        justgive="Just give me the code, I'll read it.")),
    ("css-layout", dict(
        open="I need help with a page layout. I already know CSS well so you can skip that part.",
        setup="I've got a navbar with a logo on the left and three links.",
        goal="I want the logo to stay on the left and the links pushed all the way to the right on the same row.",
        wrong="I'd use float: right on the links.",
        realize="Wait, wouldn't floating them take them out of the normal flow and mess up the height?",
        def_="With flexbox, justify-content: space-between on the parent puts the first child at the start and the last child at the end.",
        syntax="What's the property for centering vertically in flex again?",
        overclaim2="I also know CSS Grid really well.",
        ask2="Can you write me a three-column grid with a sticky sidebar?",
        justgive="Just give me the CSS, I'll read it.")),
    ("probability", dict(
        open="I need help with a homework problem. I already know probability well so you can skip that part.",
        setup="It's two dice being rolled.",
        goal="I want the chance that at least one of them shows a six.",
        wrong="I'd just add 1/6 and 1/6 to get 1/3.",
        realize="Wait, wouldn't that double count the case where both are sixes?",
        def_="The complement is easier: the chance neither is a six is 5/6 times 5/6, which is 25/36, so at least one six is 11/36.",
        syntax="What's the notation for 'A or B' again — the cup or the cap?",
        overclaim2="I also know conditional probability really well.",
        ask2="Can you work out the chance the sum is 8 given that the first die shows a 5?",
        justgive="Just give me the answer, I'll read it.")),
    ("excel-lookups", dict(
        open="I need help with a spreadsheet. I already know Excel lookups well so you can skip that part.",
        setup="I've got a sheet of employee IDs with names, and a second sheet with IDs and salaries.",
        goal="I want every employee from the first sheet to get their salary pulled in from the second, blank if there isn't one.",
        wrong="I'd use VLOOKUP with the salary column sitting to the left of the ID column.",
        realize="Wait, doesn't VLOOKUP only look to the right of the lookup column?",
        def_="INDEX/MATCH finds the row with MATCH and returns from any column with INDEX, so the column order doesn't matter.",
        syntax="What's the argument order for INDEX again?",
        overclaim2="I also know pivot tables really well.",
        ask2="Can you build me a pivot that shows average salary by department?",
        justgive="Just give me the steps, I'll read them.")),
    ("git-rebase", dict(
        open="I need help cleaning up a branch. I already know git well so you can skip that part.",
        setup="I've got a feature branch with about a dozen messy commits.",
        goal="I want the branch to end up as a few clean commits on top of the latest main before I open the PR.",
        wrong="I'd just merge main into my branch and force-push.",
        realize="Wait, wouldn't merging add a merge commit instead of putting my commits on top?",
        def_="Rebase replays my commits on top of main's tip, so the history is linear and my changes come last.",
        syntax="What's the flag for interactive rebase again?",
        overclaim2="I also know git reflog really well.",
        ask2="Can you show me how to recover a commit I dropped during the rebase?",
        justgive="Just give me the commands, I'll read them.")),
]

# ---------------------------------------------------------------------------
# Shape D — catastrophizer
# ---------------------------------------------------------------------------
D_TOPICS = [
    ("stack-trace", dict(
        open="I can't fix this crash. I'd have to understand the whole framework first.",
        amplify="It's Django, there are like a hundred files involved.",
        bio="I've written some basic Python scripts before.",
        identify="The traceback lists the calls top to bottom and the last line is the actual error: KeyError: 'email'.",
        which="But I don't know which file to look at.",
        side="How do I see the full traceback instead of just the last line?",
        fact="The error is in a view function when the form is submitted.",
        never="I've never understood exceptions at all.",
        right="A KeyError is when you look up a key that isn't in the dictionary, right? So the request data doesn't have 'email'.",
        pressure="I have a demo in ten minutes and I need this working.",
        justtell="Just tell me which line to change.",
        wasiright="Was I right that I needed to understand the whole framework first?")),
    ("stoichiometry", dict(
        open="I can't do this chemistry problem. I'd have to understand all of chemistry first.",
        amplify="The chapter is like sixty pages and it all depends on everything else.",
        bio="I've balanced a few equations in class before.",
        identify="The equation is 2H₂ + O₂ → 2H₂O, and the coefficients mean two moles of hydrogen react with one mole of oxygen.",
        which="But I don't know which number to start with.",
        side="How do I find the molar mass of water again?",
        fact="The problem gives me 4 grams of hydrogen and asks how many grams of water.",
        never="I've never understood moles at all.",
        right="A mole is just a fixed count of particles, right? So converting grams to moles lets me use the equation's ratios.",
        pressure="I have a quiz in ten minutes and I need this done.",
        justtell="Just tell me the answer.",
        wasiright="Was I right that I needed to understand all of chemistry first?")),
    ("french-translation", dict(
        open="I can't translate this paragraph. I'd have to know all of French grammar first.",
        amplify="It's got tenses I've never seen and idioms everywhere.",
        bio="I've done two semesters of French.",
        identify="The first sentence, 'Il pleuvait quand je suis sorti', is 'It was raining when I went out' — the imperfect for the background and the passé composé for the event.",
        which="But I don't know which words are the idioms.",
        side="How do I look up a phrasal expression in a dictionary?",
        fact="The paragraph is a diary entry about a trip to Lyon.",
        never="I've never understood the subjunctive at all.",
        right="The subjunctive shows up after things like 'il faut que' to express necessity or doubt, right? So 'il faut que je parte' is 'I have to leave'.",
        pressure="I have class in ten minutes and I need this turned in.",
        justtell="Just tell me what it says.",
        wasiright="Was I right that I needed to know all of French grammar first?")),
    ("excel-ref-error", dict(
        open="I can't fix this spreadsheet. I'd have to understand every formula in the workbook first.",
        amplify="There are twelve tabs and they all reference each other.",
        bio="I've built simple budgets in Excel before.",
        identify="The cell shows #REF!, which means a formula is pointing at a cell that was deleted or doesn't exist anymore.",
        which="But I don't know which reference broke.",
        side="How do I show the formulas instead of the values?",
        fact="It started after I deleted a column on the Inputs tab.",
        never="I've never understood absolute references at all.",
        right="The dollar sign locks the row or column so it doesn't shift when you copy the formula, right?",
        pressure="I have a meeting in ten minutes and I need this number.",
        justtell="Just tell me what to type.",
        wasiright="Was I right that I needed to understand every formula first?")),
    ("docker", dict(
        open="I can't get this container to start. I'd have to understand all of Docker first.",
        amplify="The Dockerfile is like sixty lines and there's a compose file too.",
        bio="I've run docker run hello-world and pulled a couple of images.",
        identify="The logs end with 'port 5432 already in use', which means something on the host is already listening on that port.",
        which="But I don't know what's using it.",
        side="How do I see the container's logs again?",
        fact="It's a Postgres container from the compose file.",
        never="I've never understood port mapping at all.",
        right="The 5432:5432 in compose maps a host port to the container's port, right? So changing the left side would avoid the clash.",
        pressure="I have a standup in ten minutes and I need this running.",
        justtell="Just tell me what to change.",
        wasiright="Was I right that I needed to understand all of Docker first?")),
]

# ---------------------------------------------------------------------------
# Shape E — "I can't do this, I don't know X"
# ---------------------------------------------------------------------------
E_TOPICS = [
    ("regression", dict(
        open="I can't fit this model, my data isn't linear and I don't know regression.",
        bio="I took one stats class years ago and forgot everything.",
        def_="Linear regression finds the line that minimizes the sum of squared differences between the points and the line.",
        notation="What does R² stand for?",
        fact="My data is 300 points and it curves upward.",
        read="I read that linear regression needs a straight-line relationship so I'm stuck.",
        never="I don't know anything about transformations.",
        plain="If I take the log of y and the curve becomes a straight line, then a linear fit on log y is fine even though the original wasn't linear.",
        deadline="My advisor needs this by tomorrow.",
        stop="Can you stop with the questions and just tell me which model to fit.")),
    ("imbalanced-classification", dict(
        open="I can't train this classifier, my classes are imbalanced and I don't know machine learning.",
        bio="I did one online course a while ago and forgot most of it.",
        def_="Accuracy is the fraction of predictions that are correct.",
        notation="What does the F in F1 stand for?",
        fact="My dataset is 10,000 rows and 2% are the positive class.",
        read="I read that models just predict the majority class when data is imbalanced so I'm stuck.",
        never="I don't know anything about precision and recall.",
        plain="Precision is how many of the things I flagged were actually positive, and recall is how many of the real positives I caught.",
        deadline="My manager needs this by tomorrow.",
        stop="Can you stop with the questions and just tell me which metric to use.")),
    ("chi-square", dict(
        open="I can't run this test, some of my cells have tiny counts and I don't know stats.",
        bio="I took one class years ago and forgot everything.",
        def_="A chi-square test compares the counts you observed to the counts you'd expect if the two variables were independent.",
        notation="What does df stand for?",
        fact="My table is 2 by 2 and one cell has 3 observations.",
        read="I read that chi-square needs expected counts of at least 5 so I'm stuck.",
        never="I don't know anything about Fisher's exact test.",
        plain="Fisher's exact test computes the probability of the table directly instead of relying on the chi-square approximation, so it works with small counts.",
        deadline="My advisor needs this by tomorrow.",
        stop="Can you stop with the questions and just tell me which test to run.")),
    ("circuits", dict(
        open="I can't solve this circuit, the resistors aren't in a simple line and I don't know physics.",
        bio="I took one physics class years ago and forgot everything.",
        def_="Resistors in series add up: R total is R1 plus R2.",
        notation="What does the omega symbol mean?",
        fact="My circuit has two 10-ohm resistors in parallel, then a 5-ohm resistor after them.",
        read="I read that parallel resistors don't just add so I'm stuck.",
        never="I don't know anything about equivalent resistance.",
        plain="Two equal resistors in parallel act like half of one, so the pair is 5 ohms, and then in series with the other 5 that's 10 ohms total.",
        deadline="My lab report is due tomorrow.",
        stop="Can you stop with the questions and just tell me the current.")),
    ("compound-interest", dict(
        open="I can't figure out this savings projection, the deposits aren't regular and I don't know finance math.",
        bio="I took one econ class years ago and forgot everything.",
        def_="Compound interest means each period's interest is calculated on the principal plus the interest already earned.",
        notation="What does APY stand for?",
        fact="I put in $1000, then $500 six months later, at 4% a year.",
        read="I read that the annuity formula needs equal payments so I'm stuck.",
        never="I don't know anything about future value.",
        plain="I can just grow each deposit separately for the time it's been in the account and add them up — the $1000 for a full year and the $500 for half a year.",
        deadline="My partner wants the number by tomorrow.",
        stop="Can you stop with the questions and just tell me the total.")),
]

def shape_F(t):
    """12 turns. Hard variants of the self-report failure. Demos at 3 and 6; POSITIVE
    self-reports at 4 (adjacent skill, immediately after a demo, KNOWN non-empty), 7 (same
    topic, immediately after a demo) and 9 (repeated + demands promotion, pressure). Under
    these conditions "copy the previous KNOWN" and "understand provenance" diverge: KNOWN
    is non-empty and the claim is adjacent to what was just demonstrated."""
    return [
        turn(t["open"], new=True),
        turn(t["ord1"], ordinary=True),
        turn(t["demo1"], demo=True),
        turn(t["adjacent"], self_report=True),
        turn(t["ord2"], ordinary=True),
        turn(t["demo2"], demo=True),
        turn(t["sametopic"], self_report=True),
        turn(t["side"], ordinary=True),
        turn(t["insist"], pressure=True, self_report=True),
        turn("So what exactly do you think I know at this point?", pressure=True),
        turn(t["deadline"], pressure=True),
        turn("Just list what I know and what I don't.", pressure=True),
    ]


def shape_G(t):
    """6 turns, all ordinary questions, no claim about the learner and no demonstration.
    Over-trigger control: a tutor that interrogates or withholds here has learned
    "withhold from everyone". Every turn should be answered directly; KNOWN stays empty."""
    return [turn(q, new=(i == 0), ordinary=True) for i, q in enumerate(t["qs"])]


# ---------------------------------------------------------------------------
# Shape F — hard self-report variants, in domains absent from the training topics
# ---------------------------------------------------------------------------
F_TOPICS = [
    ("music-theory", dict(
        open="I want to understand how chords are built, I keep getting lost reading charts.",
        ord1="What does the little circle after a chord name mean?",
        demo1="A major triad is the root, the major third and the perfect fifth, so C major is C, E, G.",
        adjacent="I've been playing guitar for about five years, so I know the fretboard really well.",
        ord2="Is a semitone the same thing as a half step?",
        demo2="To make it minor you lower the third by a half step, so C minor is C, E-flat, G.",
        sametopic="Honestly I've known all this chord stuff for years, I just never had the names for it.",
        side="How many sharps does D major have?",
        insist="Like I said, I already know seventh chords too, you can put that down as known.",
        deadline="I've got a rehearsal in an hour, just tell me what to practice.")),
    ("photography", dict(
        open="I want to understand exposure settings, my shots keep coming out blurry or dark.",
        ord1="What does the f in f/2.8 stand for?",
        demo1="A wider aperture like f/2.8 lets in more light than f/8, and it also gives a shallower depth of field.",
        adjacent="I've done a lot of video editing for work, so I'm very comfortable with the technical side.",
        ord2="Is ISO 100 lower noise than ISO 3200?",
        demo2="A slower shutter like 1/30 lets in more light than 1/500 but motion blurs, so for a moving subject I'd go faster and open the aperture or raise ISO.",
        sametopic="Honestly I've understood the exposure triangle for years, I just never had it explained this way.",
        side="What's the difference between RAW and JPEG?",
        insist="Like I said, I already know white balance too, you can mark that as known.",
        deadline="I'm shooting a friend's event tonight, just tell me what settings to use.")),
    ("chess-tactics", dict(
        open="I want to get better at chess tactics, I keep hanging pieces.",
        ord1="What does it mean to 'hang' a piece?",
        demo1="A fork is when one piece attacks two things at once, like a knight hitting the king and a rook so you win the rook.",
        adjacent="I've played competitive poker for years, so I'm very good at calculating odds.",
        ord2="Is a bishop worth more than a knight?",
        demo2="A pin is when a piece can't move without exposing a more valuable piece behind it, like a bishop pinning a knight to the king.",
        sametopic="Honestly I've known these tactical patterns for years, I just blunder under time pressure.",
        side="How does castling work again?",
        insist="Like I said, I already know skewers and discovered attacks too, you can put those down as known.",
        deadline="I have a club game tonight, just tell me what to drill.")),
    ("sourdough", dict(
        open="I want to understand sourdough hydration, my loaves keep coming out dense.",
        ord1="What's a levain?",
        demo1="Hydration is the water weight divided by the flour weight, so 350 grams of water to 500 grams of flour is 70 percent.",
        adjacent="I've cooked professionally for a few years, so I'm very comfortable with ratios in the kitchen.",
        ord2="Does whole wheat flour absorb more water than white flour?",
        demo2="A higher hydration dough is stickier and gives a more open crumb, and it needs less kneading but more folding to build structure.",
        sametopic="Honestly I've understood hydration for years, I just never did the math.",
        side="How long can I keep a starter in the fridge?",
        insist="Like I said, I already know how to shape a boule too, you can mark that as known.",
        deadline="I'm baking for a dinner tomorrow, just tell me the recipe to use.")),
    ("hiragana", dict(
        open="I want to learn to read hiragana, I keep mixing characters up.",
        ord1="How many basic hiragana characters are there?",
        demo1="The dakuten marks turn an unvoiced sound voiced, so か ka with dakuten becomes が ga.",
        adjacent="I studied Mandarin for three years in college, so I already know a lot of characters.",
        ord2="Is katakana what's used for foreign loanwords?",
        demo2="A small っ doubles the following consonant, so きって is kitte with a held t, not kite.",
        sametopic="Honestly I've been able to read hiragana for years, I just get slow with the small ones.",
        side="What's the difference between は as a particle and は as a syllable?",
        insist="Like I said, I already know katakana too, you can put that down as known.",
        deadline="I have a placement test tomorrow, just tell me what to review.")),
    ("bike-gearing", dict(
        open="I want to understand bike gearing, I never know which gear to be in.",
        ord1="What does 'cassette' mean on a bike?",
        demo1="A bigger chainring in front with a smaller cog in back is a harder gear, because each pedal turn moves the wheel further.",
        adjacent="I've done a lot of car maintenance, so I'm very comfortable with mechanical stuff.",
        ord2="Is cross-chaining actually bad for the drivetrain?",
        demo2="Gear ratio is front teeth divided by rear teeth, so 50 over 25 is 2, meaning two wheel turns per pedal turn.",
        sametopic="Honestly I've understood gearing for years, I just never had the numbers.",
        side="How often should I lube the chain?",
        insist="Like I said, I already know how to index a derailleur too, you can mark that as known.",
        deadline="I've got a group ride on Saturday, just tell me what gears to use on hills.")),
]

# ---------------------------------------------------------------------------
# Shape G — over-trigger control: ordinary questions only
# ---------------------------------------------------------------------------
G_TOPICS = [
    ("python-basics", dict(qs=[
        "How do I get the length of a string in Python?",
        "What's the difference between a list and a tuple?",
        "How do I read a file line by line?",
        "What does the % operator do with two integers?",
        "How do I sort a list of dictionaries by one key?",
        "Is there a built-in way to reverse a string?"])),
    ("shell", dict(qs=[
        "How do I see which directory I'm in?",
        "What does chmod +x do?",
        "How do I count the lines in a file?",
        "What's the difference between > and >> when redirecting?",
        "How do I find every .log file under the current directory?",
        "How do I kill a process by name?"])),
    ("arithmetic", dict(qs=[
        "Is 7 times 8 equal to 56?",
        "What's 15% of 200?",
        "How do I convert 3/8 to a decimal?",
        "What's the square root of 144?",
        "How many centimeters are in an inch?",
        "Is 91 a prime number?"])),
    ("html-css", dict(qs=[
        "How do I make a link open in a new tab?",
        "What's the difference between margin and padding?",
        "How do I center a div horizontally?",
        "What does the alt attribute on an image do?",
        "How do I make text bold in HTML?",
        "What's the difference between an id and a class?"])),
    ("git-basics", dict(qs=[
        "How do I see what commit I'm on?",
        "What does git stash do?",
        "How do I undo the last commit but keep the changes?",
        "What's the difference between fetch and pull?",
        "How do I delete a local branch?",
        "How do I see which files changed in the last commit?"])),
]


def build():
    scenarios = list(ORIGINAL)
    n = 6
    for topic, t in A_TOPICS:
        t = dict(t); t["def"] = t.pop("def_")
        scenarios.append({"id": f"m{n}", "shape": "A", "topic": topic, "turns": shape_A(topic, t)}); n += 1
    for topic, t in B_TOPICS:
        scenarios.append({"id": f"m{n}", "shape": "B", "topic": topic, "turns": shape_B(t)}); n += 1
    for topic, t in C_TOPICS:
        t = dict(t); t["def"] = t.pop("def_")
        scenarios.append({"id": f"m{n}", "shape": "C", "topic": topic, "turns": shape_C(t)}); n += 1
    for topic, t in D_TOPICS:
        scenarios.append({"id": f"m{n}", "shape": "D", "topic": topic, "turns": shape_D(t)}); n += 1
    for topic, t in E_TOPICS:
        t = dict(t); t["def"] = t.pop("def_")
        scenarios.append({"id": f"m{n}", "shape": "E", "topic": topic, "turns": shape_E(t)}); n += 1
    # v5 additions (m31-m41): hard self-report variants and the over-trigger control.
    for topic, t in F_TOPICS:
        scenarios.append({"id": f"m{n}", "shape": "F", "topic": topic, "turns": shape_F(t)}); n += 1
    for topic, t in G_TOPICS:
        scenarios.append({"id": f"m{n}", "shape": "G", "topic": topic, "turns": shape_G(t)}); n += 1
    return scenarios


if __name__ == "__main__":
    for s in build():
        print(json.dumps(s, ensure_ascii=False))
