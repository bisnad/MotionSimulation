/** \file dab_com_mocap_swarm_listener.cpp
*/

#include "dab_com_mocap_swarm_listener.h"
#include "dab_flock_simulation.h"
#include "dab_flock_swarm.h"
#include "dab_flock_agent.h"
#include "dab_flock_parameter.h"
#include "dab_flock_event_includes.h"

using namespace dab;
using namespace dab::com;
using namespace dab::flock;

MocapSwarmListener::MocapSwarmListener(const std::string& pFlockName)
	: OscListener()
	, mFlockName(pFlockName)
{}

MocapSwarmListener::~MocapSwarmListener()
{}

void
MocapSwarmListener::notify(std::shared_ptr<OscMessage> pMessage)
{
	mLock.lock();

	//std::cout << "MocapSwarmListener::notify\n";

	mMessageQueue.push_back(pMessage);
	if (mMessageQueue.size() > mMaxMessageQueueLength) mMessageQueue.pop_front();

	mLock.unlock();
}

void
MocapSwarmListener::update()
{
	mLock.lock();

	while (mMessageQueue.size() > 0)
	{
		std::shared_ptr< OscMessage > oscMessage = mMessageQueue[0];

		update(oscMessage);

		mMessageQueue.pop_front();
	}

	mLock.unlock();
}

void
MocapSwarmListener::update(std::shared_ptr<OscMessage> pMessage)
{
	try
	{
		//std::cout << "MocapSwarmListener::update\n";

		std::string address = pMessage->address();

		//std::cout << "address " << address << "\n";

		const std::vector<_OscArg*>& arguments = pMessage->arguments();

		if (address.compare("/mocap/joint/pos") == 0) updateMocapFlockPositions(arguments); // Qualisys version
		if (address.compare("/mocap/joint/pos_world") == 0) updateMocapFlockPositions(arguments); // XSens version
		if (address.compare("/mocap/joint/velocity") == 0) updateMocapFlockVelocities(arguments);
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}
}

void
MocapSwarmListener::updateMocapFlockPositions(const std::vector<_OscArg*>& pArgs) throw (dab::Exception)
{
	//std::cout << "updateMocapFlockPositions\n";

	int argCount = pArgs.size();

	if (argCount % 3 != 0) throw dab::Exception("COM ERROR: arguments received not a multiple of 3", __FILE__, __FUNCTION__, __LINE__);

	int posCount = argCount / 3;

	try
	{
		dab::flock::Simulation& simulation = dab::flock::Simulation::get();
		Swarm* swarm = simulation.swarm("mocap_swarm");
		int agentCount = swarm->agentCount();

		if (agentCount != posCount) throw dab::Exception("COM ERROR: number of joint positions " + std::to_string(posCount) + " does not match number of agents " + std::to_string(agentCount), __FILE__, __FUNCTION__, __LINE__);

		// set agent positions to joint positions
		int posParIndex = swarm->parameterIndex("position");
		std::vector<dab::flock::Agent*>& agents = swarm->agents();
		std::array<float, 3> jointPos;

		for (int agentI = 0, argI=0; agentI < agentCount; ++agentI, argI += 3)
		{
			dab::flock::Parameter* posPar = agents[agentI]->parameter(posParIndex);

			jointPos[0] = *pArgs[argI];
			jointPos[1] = *pArgs[argI + 1];
			jointPos[2] = *pArgs[argI+2];

			/*
			jointPos[0] *= -0.01; // from cm to m
			jointPos[1] *= 0.01; // from cm to m and flip axis
			jointPos[2] *= 0.01; // from cm to m
			*/

			jointPos[0] *= -1.0; // from cm to m
			//jointPos[1] *= 1.0; // from cm to m and flip axis
			//jointPos[2] *= 1.0; // from cm to m

			posPar->setValues(3, jointPos.data());

			//std::cout << "aI " << agentI << " pos " << jointPos[0] << " " << jointPos[1] << " " << jointPos[2] << "\n";
		}

	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("COM ERROR: failed to update mocap flock positions", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}


	//if (pArgs.size() == 1)
	//{
	//	float gravity = *pArgs[0];

	//	physics::Simulation& physics = physics::Simulation::get();

	//	physics.setGravity(glm::vec3(0.0, 0.0, gravity));
	//}
	//else if (pArgs.size() == 3)
	//{
	//	glm::vec3 gravity;
	//	gravity[0] = *pArgs[0];
	//	gravity[1] = *pArgs[1];
	//	gravity[2] = *pArgs[2];

	//	physics::Simulation& physics = physics::Simulation::get();

	//	physics.setGravity(gravity);
	//}
	//else throw(dab::Exception("Osc Error: Wrong Parameters for /physics/sim/gravity", __FILE__, __FUNCTION__, __LINE__));
}

void
MocapSwarmListener::updateMocapFlockVelocities(const std::vector<_OscArg*>& pArgs) throw (dab::Exception)
{
	//std::cout << "updateMocapFlockVelocities\n";

	int argCount = pArgs.size();

	if (argCount % 3 != 0) throw dab::Exception("COM ERROR: arguments received not a multiple of 3", __FILE__, __FUNCTION__, __LINE__);

	int velCount = argCount / 3;

	try
	{
		dab::flock::Simulation& simulation = dab::flock::Simulation::get();
		Swarm* swarm = simulation.swarm("mocap_swarm");
		int agentCount = swarm->agentCount();

		if (agentCount != velCount) throw dab::Exception("COM ERROR: number of joint velocties " + std::to_string(velCount) + " does not match number of agents " + std::to_string(agentCount), __FILE__, __FUNCTION__, __LINE__);

		// set agent positions to joint positions
		int velParIndex = swarm->parameterIndex("velocity");
		std::vector<dab::flock::Agent*>& agents = swarm->agents();
		std::array<float, 3> jointVel;

		for (int agentI = 0, argI = 0; agentI < agentCount; ++agentI, argI += 3)
		{
			dab::flock::Parameter* velPar = agents[agentI]->parameter(velParIndex);

			jointVel[0] = *pArgs[argI];
			jointVel[1] = *pArgs[argI + 1];
			jointVel[2] = *pArgs[argI + 2];

			jointVel[0] *= -0.01; // from cm to m
			jointVel[1] *= 0.01; // from cm to m and flip axis
			jointVel[2] *= 0.01; // from cm to m

			velPar->setValues(3, jointVel.data());

			//std::cout << "aI " << agentI << " pos " << jointPos[0] << " " << jointPos[1] << " " << jointPos[2] << "\n";
		}

	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("COM ERROR: failed to update mocap flock velocities", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}


	//if (pArgs.size() == 1)
	//{
	//	float gravity = *pArgs[0];

	//	physics::Simulation& physics = physics::Simulation::get();

	//	physics.setGravity(glm::vec3(0.0, 0.0, gravity));
	//}
	//else if (pArgs.size() == 3)
	//{
	//	glm::vec3 gravity;
	//	gravity[0] = *pArgs[0];
	//	gravity[1] = *pArgs[1];
	//	gravity[2] = *pArgs[2];

	//	physics::Simulation& physics = physics::Simulation::get();

	//	physics.setGravity(gravity);
	//}
	//else throw(dab::Exception("Osc Error: Wrong Parameters for /physics/sim/gravity", __FILE__, __FUNCTION__, __LINE__));
}