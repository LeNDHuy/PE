import random
import simpy
import numpy as np
from random import seed
import statistics

seed(29384)  # for seed of randint function
random_seed = 42  # for seed of other random generators
new_customers = 30  # Total number of new customers would be generated in the system
server_number = 2  # Total number of server each service queue in the system has
max_customers = 10  # Total number of customers the store can handle
max_actions_number = (
    10  # Maximum amount of actions a customer can take before checking out
)


class BuffetService:
    class Customer:
        def set_name(self, name):
            self.name = name

        def get_name(self):
            return self.name

        def get_actions_number(self):
            return self.actions_number

        def set_actions_number(self, number):
            self.actions_number = number

        def decrease_actions_number(self):
            self.actions_number -= 1
            return self.actions_number

        def get_arrive_time(self):
            return self.arrive_time

        def set_arrive_time(self, time):
            self.arrive_time = time

        def add_to_logs(self, log_entry):
            self.logs.append(log_entry)

        def print_logs(self):
            if len(self.logs) > 0:
                for log_entry in self.logs:
                    print("%s" % log_entry)
            else:
                print("No logs to print")

        def __init__(self, id, actions_number):
            self.id = id
            self.logs = []
            self.name = "Customer%02d" % id
            self.arrive_time = 0
            self.actions_number = actions_number

    class Service:
        def serve(self, customer, service_time):
            arrive = self.env.now
            name = customer.get_name()
            self.waitingQueue.append(name)
            if self.arrive_before != 0:
                self.interArrivalTimes.append(arrive - self.arrive_before)
            self.arrive_before = arrive
            customer.add_to_logs(
                "%7.4f :  %s arrived at %s" % (arrive, name, self.serviceName)
            )
            print("%7.4f :  %s arrived at %s" % (arrive, name, self.serviceName))
            while 1:
                with self.server.request() as req:
                    results = yield req | self.env.timeout(
                        statistics.mean(self.serviceTimes)
                    )
                    if req in results:
                        if name in self.waitingQueue[0]:
                            self.waitingQueue.pop(0)
                            starttime = self.env.now
                            waiting_time = starttime - arrive
                            self.waitingTimes.append(waiting_time)
                            servertime = service_time
                            self.serviceTimes.append(servertime)
                            yield self.env.timeout(servertime)
                            customer.add_to_logs(
                                "%7.4f: %s left %s"
                                % (self.env.now, name, self.serviceName)
                            )
                            print(
                                "%7.4f: %s left %s"
                                % (self.env.now, name, self.serviceName)
                            )
                            # print("%6.3f Waiting time of %s" % (waiting_time, name))
                            # print(
                            #     "%7.4f Time Spent in the system of %s"
                            #     % (env.now - arrive, name)
                            # )
                            # self.env.process(
                            #     self.outer_instance.check_out(
                            #         self.env, starttime, customer.id
                            #     )
                            # )
                            # self.env.process(
                            self.outer_instance.route(
                                customer.id, self.serviceId, service_time=0.15
                            )
                            # )
                            break

        def get_mean_waiting_time(self):
            return statistics.mean(self.waitingTimes)

        def get_mean_service_time(self):
            return statistics.mean(self.serviceTimes)

        def get_mean_inter_arrival_time(self):
            return statistics.mean(self.interArrivalTimes)

        def get_report(self):
            print()
            print("%s's report:" % self.serviceName)
            print(
                "Average Inter Arrival Time Is : %7.4f"
                % self.get_mean_inter_arrival_time()
            )
            print("Average Service Time Is : %7.4f" % self.get_mean_service_time())

            if len(self.waitingTimes) > 0:
                average_waitingTime = self.get_mean_waiting_time()
                print("Average Waiting Time Is : %7.4f" % average_waitingTime)

        def get_service_name(self):
            return self.serviceName

        def __init__(self, env, serviceId, serviceName, server_number, outer_instance):
            self.env = env
            self.arrive_before = 0
            self.waitingQueue = []
            self.waitingTimes = []
            self.serviceTimes = []
            self.interArrivalTimes = []
            self.serviceId = serviceId
            self.serviceName = serviceName
            self.serviceTimes.append(0)
            self.interArrivalTimes.append(0)
            self.servers_number = server_number
            self.outer_instance = outer_instance
            self.server = simpy.Resource(env, capacity=server_number)

    def route(self, customerId, serviceId, service_time):
        available_actions_number = self.customersList[
            customerId
        ].decrease_actions_number()
        if available_actions_number > 0:
            random_choice = random.randint(1, 5)
            while random_choice == serviceId:
                random_choice = random.randint(1, 5)

            service = self.servicesList[random_choice - 1]

            s = service.serve(
                self.customersList[customerId],
                service_time=random.expovariate(service_time),
            )
            self.env.process(s)
        else:
            self.env.process(self.check_out(self.env, customerId))

    def check_out(self, env, customerId):
        # arrive = env.now
        current_customer = self.customersList[customerId]
        # waiting_time = starttime - current_customer.get_arrive_time()
        name = current_customer.get_name()
        # self.waitingTimes.append(waiting_time)
        self.waitingQueueCheckOut.append(name)
        while 1:
            with self.server.request() as req:
                results = yield req | env.timeout(statistics.mean(self.serviceTimes))
                if req in results:
                    if name in self.waitingQueueCheckOut[0]:
                        self.waitingQueueCheckOut.pop(0)
                        current_customer.add_to_logs(
                            "%7.4f: %s left the store" % (env.now, name)
                        )
                        print("%7.4f: %s left the store" % (env.now, name))
                        # print("%6.3f Waiting time of %s" % (waiting_time, name))
                        current_customer.add_to_logs(
                            "Time Spent in the store of %s: %7.4f"
                            % (
                                name,
                                env.now - current_customer.get_arrive_time(),
                            )
                        )
                        print(
                            "Time Spent in the store of %s: %7.4f"
                            % (
                                name,
                                env.now - current_customer.get_arrive_time(),
                            )
                        )
                        self.available_slots += 1
                        break
                    else:
                        env.timeout(statistics.mean(self.serviceTimes))

    def entry(self, env, customerId, name, service_time):
        current_customer = self.customersList[customerId]
        current_customer.set_arrive_time(env.now)
        arrive = current_customer.get_arrive_time()
        self.waitingQueueEntry.append(name)
        current_customer.add_to_logs("%7.4f : %s arrived at the store" % (arrive, name))
        print("%7.4f : %s arrived at the store" % (arrive, name))
        while 1:
            if self.available_slots > 0:
                # with server.request() as req:
                #     results = yield req | env.timeout(
                #         statistics.mean(self.serviceTimes)
                #     )
                #     if req in results:
                # print(self.available_slots)
                if name in self.waitingQueueEntry[0]:
                    self.available_slots -= 1
                    self.waitingQueueEntry.pop(0)
                    starttime = env.now
                    self.waitingTimes.append(starttime - arrive)
                    servertime = service_time
                    self.serviceTimes.append(servertime)
                    yield env.timeout(servertime)
                    self.route(customerId, 0, service_time=0.15)
                    break
                else:
                    yield env.timeout(statistics.mean(self.serviceTimes))
            else:
                yield env.timeout(statistics.mean(self.serviceTimes))

    # def customer(self, env, customerId, name, server, service_time):
    #     # customer arrives to the system, waits and leaves
    #     arrive = env.now
    #     self.waitingQueueEntry.append(name)
    #     print("%7.4f : Arrival time of %s" % (arrive, name))
    #     while 1:
    #         with server.request() as req:
    #             results = yield req | env.timeout(statistics.mean(self.serviceTimes))
    #             if req in results:
    #                 if name in self.waitingQueueEntry[0]:
    #                     self.waitingQueueEntry.pop(0)
    #                     starttime = env.now
    #                     servertime = service_time
    #                     self.serviceTimes.append(servertime)
    #                     yield env.timeout(servertime)
    #                     waiting_time = starttime - arrive
    #                     self.waitingTimes.append(waiting_time)
    #                     print("%7.4f Departure Time of %s" % (env.now, name))
    #                     print("%6.3f Waiting time of %s" % (waiting_time, name))
    #                     print(
    #                         "%7.4f Time Spent in the system of %s"
    #                         % (env.now - arrive, name)
    #                     )
    #                     break

    def generator(
        self, env, number, interval, service_time
    ):  # customer generator with interarrival times.
        """generator generates customers randomly"""
        for i in range(number):
            actions_number = random.randint(2, max_actions_number)
            self.customersList.insert(
                i,
                self.Customer(i, actions_number),
            )
            e = self.entry(
                env,
                i,
                self.customersList[i].get_name(),
                service_time=random.expovariate(service_time),
            )
            self.customersList[i].add_to_logs("%7.4f: Generated" % env.now)
            # s = self.service1.serve(
            #     self.customersList[i], service_time=random.expovariate(service_time)
            # )
            env.process(e)
            t = random.expovariate(1.0 / interval)
            yield env.timeout(
                t
            )  # adds time to the counter, does not delete from the memory

    def get_service_mean_service_time(self):
        services_serviceTimes = []
        for service in self.servicesList:
            services_serviceTimes.append(service.get_mean_service_time())
        return statistics.mean(services_serviceTimes)

    def get_service_mean_waiting_time(self):
        services_waitingTimes = []
        for service in self.servicesList:
            services_waitingTimes.append(service.get_mean_waiting_time())
        return statistics.mean(services_waitingTimes)

    def get_service_mean_inter_arrival_time(self):
        services_interArrivalTimes = []
        for service in self.servicesList:
            services_interArrivalTimes.append(service.get_mean_inter_arrival_time())
        return statistics.mean(services_interArrivalTimes)

    def get_entry_report(self):
        average_interarrival = statistics.mean(self.interarrivalTimes)
        average_serviceTime = statistics.mean(self.serviceTimes)
        print()
        print("The Entrance's report:")
        print("Average Interarrival Time Is : %7.4f" % average_interarrival)
        print("Average Service Time Is : %7.4f" % average_serviceTime)

        if len(self.waitingTimes) > 0:
            average_waitingTime = statistics.mean(self.waitingTimes)
            print("Average Waiting Time Is : %7.4f" % average_waitingTime)

    def get_total_report(self):
        print()
        print("The Store's report:")
        print(
            "Average Inter Arrival Time Is : %7.4f"
            % self.get_service_mean_inter_arrival_time()
        )
        print("Average Service Time Is : %7.4f" % self.get_service_mean_service_time())
        print("Average Waiting Time Is : %7.4f" % self.get_service_mean_waiting_time())

    def get_service_report(self, serviceId):
        if serviceId <= 0:
            print("Invalid Service Id")
            return
        service = self.servicesList[serviceId - 1]
        print()
        print("%s's report:" % service.get_service_name())
        print(
            "Average Inter Arrival Time Is : %7.4f"
            % service.get_mean_inter_arrival_time()
        )
        print("Average Service Time Is : %7.4f" % service.get_mean_service_time())
        print("Average Waiting Time Is : %7.4f" % service.get_mean_waiting_time())

    def print_customer_log(self, customerId):
        self.customersList[customerId].print_logs()

    def run(self):
        self.env.run()

    def __init__(self, customer_number, max_customers, server_number):
        self.customersList = []
        self.servicesList = []
        self.customer_number = customer_number
        self.available_slots = max_customers
        self.interarrival = np.random.poisson(6, size=None)
        self.waitingTimes = []
        # self.waitingTimesCheckOut = []
        self.serviceTimes = []
        # self.serviceTimesCheckOut = []
        self.interarrivalTimes = []
        # self.interarrivalTimesCheckOut = []
        self.waitingQueueEntry = []
        self.waitingQueueCheckOut = []
        self.env = simpy.Environment()
        self.server = simpy.Resource(
            self.env, capacity=1
        )  # capacity changes the number of generators in the system.
        self.orderFood = self.Service(
            self.env, 1, "Food Ordering Service", server_number, self
        )
        self.orderDrink = self.Service(
            self.env, 2, "Drink Ordering Service", server_number, self
        )
        self.meatStall = self.Service(self.env, 3, "Meat Stall", server_number, self)
        self.vegetableStall = self.Service(
            self.env, 4, "Vegetable Stall", server_number, self
        )
        self.drinkStall = self.Service(self.env, 5, "Drink Stall", server_number, self)
        self.serviceTimes.append(0)
        self.interarrivalTimes.append(self.interarrival)
        self.servicesList.append(self.orderFood)
        self.servicesList.append(self.orderDrink)
        self.servicesList.append(self.meatStall)
        self.servicesList.append(self.vegetableStall)
        self.servicesList.append(self.drinkStall)
        self.env.process(
            self.generator(
                self.env,
                self.customer_number,
                self.interarrival,
                service_time=0.15,
            )
        )


buffet1 = BuffetService(new_customers, max_customers, server_number)
buffet1.run()

for i in range(new_customers):
    print()
    print("Customer%02d's routes:" % i)
    buffet1.print_customer_log(i)

buffet1.get_entry_report()
buffet1.get_total_report()
for i in range(1, 5):
    buffet1.get_service_report(i)
