/** \file dab_com_mocap_swarm_listener.h
*/

#pragma once

/** \file dab_com_physics_osc_control.h
*/

#pragma once

#include "dab_singleton.h"
#include "dab_osc_receiver.h"
#include <mutex>

namespace dab
{

	namespace com
	{

		class MocapSwarmListener : public OscListener
		{
		public:
			MocapSwarmListener(const std::string& pFlockName);
			~MocapSwarmListener();

			void notify(std::shared_ptr<OscMessage> pMessage);
			void update();
			void update(std::shared_ptr<OscMessage> pMessage);

		protected:
			std::string mFlockName;

			unsigned int mMaxMessageQueueLength = 2048;
			std::deque< std::shared_ptr<OscMessage> > mMessageQueue;

			void updateMocapFlockPositions(const std::vector<_OscArg*>& pArgs) throw (dab::Exception);
			void updateMocapFlockVelocities(const std::vector<_OscArg*>& pArgs) throw (dab::Exception);

			std::mutex mLock;
		};

	};

};

