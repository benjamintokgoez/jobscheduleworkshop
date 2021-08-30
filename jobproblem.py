from typing import List
from azure.quantum.optimization import Term
from azure.quantum import Workspace
from azure.quantum.optimization import Problem, ProblemType
from azure.quantum.optimization import QuantumMonteCarlo

workspace = Workspace (
      subscription_id = "###",
  resource_group = "###",
  name = "##",
  location = "##"
)

workspace.login()



processingTime = {0: 2, 1: 1, 2: 3, 3: 5, 4: 2, 5: 3, 6: 2, 7: 2, 8: 3, 9: 2} #slide config

jobsOpsMap = {0: [0, 1, 2],1: [3, 4, 5],2: [6, 7, 8, 9]}

opsJobMap = {
    0:1,
    1:1,
    2:1,
    3:2,
    4:2,
    5:2,
    6:3,
    7:3,
    8:3,
    9:3
}

toolsOpsMap = {0: [0, 1, 3, 4, 6, 7],1: [2, 5, 8],2: [9]}

alpha = 1
beta = 1
gamma = 1
delta = 1

T = sum(processingTime.values())

#f(x), weight = alpha
def precedenceConstraint():

    terms = []
    for job in jobsOpsMap.values():
        for op in range(len(job) -1):
            for t in range(0, T):
                for s in range(0, min(t + processingTime[job[op]], T)):
                    terms.append(Term(c=alpha, indices=[job[op]*T+t, job[op+1]*T+s]))
    return terms

#g(x), weight = beta
def operationOnceConstraint():

    terms = []
    for op in opsJobMap.keys():
        for t in range(0, T):
            #2xy - x - y + 1
            #-x-y
             terms.append(Term(c=beta*-1, indices=[op*T+t]))
             for s in range(t+1, T):
                 #2xy
                 terms.append(Term(c=beta*2, indices=[op*T+t, op*T+s]))
    #+1
    terms.append(Term(c=beta*1, indices=[]))
    return terms

#h(x), weight=gamma
def noOverlapConstraint():
#toolsOpsMap = {0: [0, 1, 3, 4, 6, 7],1: [2, 5, 8],2: [9]}
    terms = []
    for op in toolsOpsMap.values():
        for i in op:
            for k in op:
                if i!=k:
                    for t in range(0, T):
                    #error duplicate
                    
                        #    terms.append(Term(c=gamma, indices=[i*T+t, k*T+t]))

                        for s in range(t, min(t + processingTime[i], T)):
                            terms.append(Term(c=gamma, indices=[i*T+t, k*T+s]))
    return terms

#copied   
def calcPenalty(t:int, lowerBound:int):
    toolsCount = len(toolsOpsMap)
    return (toolsCount**(t-lowerBound)-1)/(toolsCount-1)

#k(x), weight = delta
def makespanObjective():

    terms = []

    lowerBound = max([sum([processingTime[i] for i in job]) for job in jobsOpsMap.values()])

    for job in jobsOpsMap.values():
        op = job[-1]

        for t in range(lowerBound + 1, T + processingTime[op]):
            penalty = calcPenalty(t, lowerBound)
            terms.append(Term(c=delta*penalty, indices=[op*T + (t - processingTime[op])]))

    return terms

def submit():
    terms = precedenceConstraint() + operationOnceConstraint() + noOverlapConstraint() + makespanObjective()

    problem = Problem(name = "Workshop Test", problem_type=ProblemType.pubo, terms=terms)

    #solver = SimulatedAnnealing(workspace, timeout=100)
    solver = QuantumMonteCarlo(workspace, sweeps = 10, trotter_number = 10, restarts = 72, seed = 22, beta_start = 0.1, transverse_field_start = 10, transverse_field_stop = 0.1)

    job = solver.submit(problem)
    job.refresh()

    results = job.get_results()
    config = results['configuration']
    print(config)


submit()
