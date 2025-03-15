/** \file dab_physics_behavior_rotation_target_oscil.h
*/

#pragma once

#include "dab_physics_behavior.h"
#include "ofVectorMath.h"

#include <array>

namespace dab
{
	namespace physics
	{
		class BodyMotor;

		class RotationTargetOscilBehavior : public Behavior
		{
		public:
			RotationTargetOscilBehavior(const std::string& pName, const std::vector<std::shared_ptr<BodyPart>>& pParts, const std::vector<std::shared_ptr<BodyJoint>>& pJoints, const std::vector<std::shared_ptr<BodyMotor>>& pMotors);

			void update() throw (Exception);

		protected:

			void init();
			void notifyParameterChange(const std::string& pParName);

			Value< std::array<float, 3> > mTarget1;
			Value< std::array<float, 3> > mTarget2;
			Value<float> mSpeed;
			Value<float> mOscilInterval;
			Value<float> mApplicationInterval;


			int mCurrentTargetIndex;
			double mLastOscilTime;
			double mLastApplicationTime;
		};

	};

};