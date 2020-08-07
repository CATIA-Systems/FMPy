#pragma once

#include "rpc/msgpack.hpp"
#include <string>
#include <vector>

struct LogMessage {
	std::string instanceName;
	int status;
	std::string category;
	std::string message;
	MSGPACK_DEFINE_ARRAY(instanceName, status, category, message)
};

struct ReturnValue {
	int status;
	std::list<LogMessage> logMessages;
	MSGPACK_DEFINE_ARRAY(status, logMessages)
};

struct RealReturnValue {
	int status;
	std::list<LogMessage> logMessages;
	std::vector<double> value;
	MSGPACK_DEFINE_ARRAY(status, logMessages, value)
};

struct IntegerReturnValue {
	int status;
	std::list<LogMessage> logMessages;
	std::vector<int> value;
	MSGPACK_DEFINE_ARRAY(status, logMessages, value)
};

struct EventInfoReturnValue {
	int status;
	std::list<LogMessage> logMessages;
	int newDiscreteStatesNeeded;
	int terminateSimulation;
	int nominalsOfContinuousStatesChanged;
	int valuesOfContinuousStatesChanged;
	int nextEventTimeDefined;
	double nextEventTime;
	MSGPACK_DEFINE_ARRAY(status, logMessages, newDiscreteStatesNeeded, terminateSimulation, nominalsOfContinuousStatesChanged, valuesOfContinuousStatesChanged, nextEventTimeDefined, nextEventTime)
};
