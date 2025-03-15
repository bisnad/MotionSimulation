/** \file dab_physics_state.cpp
*/

#include "dab_physics_state.h"
#include "dab_physics_simulation.h"
#include "dab_physics_body.h"
#include "dab_physics_body_part.h"
#include "dab_physics_body_joint.h"
#include "dab_physics_universal_joint.h"
#include "dab_physics_body_motor.h"
#include "dab_physics_universal_motor.h"
#include "dab_physics_behavior.h"
#include "dab_physics_state_serialize.h"
#include "ofUtils.h"
#include "ofMath.h"

using namespace dab;
using namespace dab::physics;

# pragma mark StateEffect Definition

StateEffect::StateEffect(StateEffectType pEffectType, const std::vector<std::string>& pBodyNames, const std::vector<std::string>& pTargetNames, const std::string& pParameterName, const AbstractValue& pParameterValue)
	: mEffectType(pEffectType)
	, mBodyNames(pBodyNames)
	, mTargetNames(pTargetNames)
	, mParameterName(pParameterName)
	, mParameterValue(pParameterValue.copy())
{
	try
	{
		init();
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}
}


StateEffect::StateEffect(const StateEffect& pStateEffect)
	: mEffectType(pStateEffect.mEffectType)
	, mBodyNames(pStateEffect.mBodyNames)
	, mTargetNames(pStateEffect.mTargetNames)
	, mParameterName(pStateEffect.mParameterName)
	, mParameterValue(pStateEffect.mParameterValue->copy())
{
	try
	{
		init();
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}
}

const StateEffect& 
StateEffect::operator=(const StateEffect& pStateEffect)
{
	mEffectType = pStateEffect.mEffectType;
	mBodyNames = pStateEffect.mBodyNames;
	mTargetNames = pStateEffect.mTargetNames;
	mParameterName = pStateEffect.mParameterName;
	mParameterValue = std::shared_ptr<AbstractValue>(pStateEffect.mParameterValue->copy());

	try
	{
		init();
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}

	return *this;
}

StateEffectType 
StateEffect::effectType() const
{
	return mEffectType;
}

const std::vector<std::string>& 
StateEffect::bodyNames() const
{
	return mBodyNames;
}

const std::vector<std::string>& 
StateEffect::targetNames() const
{
	return mTargetNames;
}

const std::string& 
StateEffect::parameterName() const
{
	return mParameterName;
}

const std::shared_ptr<AbstractValue> 
StateEffect::parameterValue() const
{
	return mParameterValue;
}

void 
StateEffect::changeBodies(const std::vector<std::string>& pBodyNames)
{
	mBodyNames = pBodyNames;

	try
	{
		init();
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}
}

void 
StateEffect::changeTargets(const std::vector<std::string>& pTargetNames)
{
	mTargetNames = pTargetNames;

	try
	{
		init();
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}
}

void 
StateEffect::changeParameterName(const std::string& pParameterName)
{
	mParameterName = pParameterName;
}

void 
StateEffect::changeParameterValue(const AbstractValue& pParameterValue)
{
	mParameterValue = std::shared_ptr<AbstractValue>(pParameterValue.copy());
}

void
StateEffect::init() throw(dab::Exception)
{
	try
	{
		if (mEffectType == BodyPartEffect) mBodyParts = gatherParts();
		else if (mEffectType == BodyJointEffect) mBodyJoints = gatherJoints();
		else if (mEffectType == BodyMotorEffect) mBodyMotors = gatherMotors();
		else if (mEffectType == BodyBehaviorEffect) mBodyBehaviors = gatherBehaviors();
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to initialize state effect", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}
}

void 
StateEffect::apply() throw(dab::Exception)
{
	try
	{
		if (mEffectType == BodyPartEffect)
		{
			//std::cout << "Apply Body Part Effects\n";

			for (auto part : mBodyParts)
			{
				//std::cout << "body " << part->body()->name() << " part " << part->name() << " par " << mParameterName << " value " << *mParameterValue << "\n";

				part->set(mParameterName, *mParameterValue);
			}
		}
		else if(mEffectType == BodyJointEffect)
		{
			//std::cout << "Apply Body Joint Effects\n";

			for (auto joint : mBodyJoints)
			{
				//std::cout << "body " << joint->body()->name() << " joint " << joint->name() << " par " << mParameterName << " value " << *mParameterValue << "\n";

				joint->set(mParameterName, *mParameterValue);
			}
		}
		else if (mEffectType == BodyMotorEffect)
		{
			//std::cout << "Apply Body Motor Effects\n";

			for (auto motor : mBodyMotors)
			{
				//std::cout << "body " << motor->body()->name() << " motor " << motor->name() << " par " << mParameterName << " value " << *mParameterValue << "\n";

				motor->set(mParameterName, *mParameterValue);
			}
		}
		else if (mEffectType == BodyBehaviorEffect)
		{
			//std::cout << "Apply Body Behavior Effects\n";

			for (auto behavior : mBodyBehaviors)
			{
				//std::cout << "body " << behavior->body()->name() << " behavior " << behavior->name() << " par " << mParameterName << " value " << *mParameterValue << "\n";

				behavior->set(mParameterName, *mParameterValue);
			}
		}
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to apply state effect", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}
}

std::vector<std::shared_ptr<BodyPart>>
StateEffect::gatherParts() throw(dab::Exception)
{
	try
	{
		if (mEffectType != BodyPartEffect) throw dab::Exception("Physics Error: effect type doesn't operate on body parts", __FILE__, __FUNCTION__, __LINE__);

		dab::physics::Simulation& physics = dab::physics::Simulation::get();

		std::vector<std::shared_ptr<BodyPart>> parts;

		for (auto bodyName : mBodyNames)
		{
			std::shared_ptr<Body> body = physics.body(bodyName);

			for (auto partName : mTargetNames)
			{
				std::shared_ptr<BodyPart> part = body->part(partName);
				parts.push_back(part);
			}
		}

		return parts;
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to gather body parts", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}
}

std::vector<std::shared_ptr<BodyJoint>> 
StateEffect::gatherJoints() throw (dab::Exception)
{
	try
	{
		if (mEffectType != BodyJointEffect) throw dab::Exception("Physics Error: effect type doesn't operate on body joints", __FILE__, __FUNCTION__, __LINE__);

		dab::physics::Simulation& physics = dab::physics::Simulation::get();

		std::vector<std::shared_ptr<BodyJoint>> joints;

		for (auto bodyName : mBodyNames)
		{
			std::shared_ptr<Body> body = physics.body(bodyName);

			for (auto jointName : mTargetNames)
			{
				std::shared_ptr<BodyJoint> joint = body->joint(jointName);
				joints.push_back(joint);
			}
		}

		return joints;
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to gather body joints", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}
}

std::vector<std::shared_ptr<BodyMotor>> 
StateEffect::gatherMotors() throw (dab::Exception)
{
	try
	{
		if (mEffectType != BodyMotorEffect) throw dab::Exception("Physics Error: effect type doesn't operate on body motors", __FILE__, __FUNCTION__, __LINE__);

		dab::physics::Simulation& physics = dab::physics::Simulation::get();

		std::vector<std::shared_ptr<BodyMotor>> motors;

		for (auto bodyName : mBodyNames)
		{
			std::shared_ptr<Body> body = physics.body(bodyName);

			for (auto motorName : mTargetNames)
			{
				std::shared_ptr<BodyMotor> motor = body->motor(motorName);
				motors.push_back(motor);
			}
		}

		return motors;
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to gather body motors", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}
}

std::vector<std::shared_ptr<Behavior>> 
StateEffect::gatherBehaviors() throw (dab::Exception)
{
	try
	{
		if (mEffectType != BodyBehaviorEffect) throw dab::Exception("Physics Error: effect type doesn't operate on body behaviors", __FILE__, __FUNCTION__, __LINE__);

		dab::physics::Simulation& physics = dab::physics::Simulation::get();

		std::vector<std::shared_ptr<Behavior>> behaviors;

		for (auto bodyName : mBodyNames)
		{
			std::shared_ptr<Body> body = physics.body(bodyName);

			for (auto behaviorName : mTargetNames)
			{
				std::shared_ptr<Behavior> behavior = body->behavior(behaviorName);
				behaviors.push_back(behavior);
			}
		}

		return behaviors;
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to gather behaviors", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}
}

StateEffect::operator std::string() const
{
	return info();
}

std::string
StateEffect::info() const
{
	std::stringstream ss;

	if(mEffectType == BodyPartEffect) ss << "effect type BodyPartEffect\n";
	else if (mEffectType == BodyJointEffect) ss << "effect type BodyJointEffect\n";
	else if (mEffectType == BodyMotorEffect) ss << "effect type BodyMotorEffect\n";
	else if (mEffectType == BodyBehaviorEffect) ss << "effect type BodyBehaviorEffect\n";

	ss << "body names: ";
	for (auto bodyName : mBodyNames) ss << bodyName << " ";
	ss << "\n";
	ss << "target names: ";
	for (auto targetName : mTargetNames) ss << targetName << " ";
	ss << "\n";
	ss << "parameter name: " << mParameterName << "\n";
	ss << "parameter value: " << *mParameterValue << "\n";

	return ss.str();
}

# pragma mark State definition

State::State(const std::string& pStateName)
	: mName(pStateName)
	, mParentState(nullptr)
	, mActive(true)
{}

State::State(const State& pState)
	: mName(pState.mName)
	, mParentState(nullptr)
	, mActive(pState.mActive)
{
	if (pState.mParentState != nullptr)
	{
		mParentState = std::shared_ptr<State>( new State(*(pState.mParentState)) );
	}

	for (auto effect : pState.mStateEffects)
	{
		mStateEffects.push_back( std::shared_ptr<StateEffect>( new StateEffect(*effect) ) );
	}

	for (auto subState : pState.mSubStates)
	{
		mSubStates.push_back( std::shared_ptr<State>( new State(*subState) ) );
	}
}

const State& 
State::operator=(const State& pState)
{
	mName = pState.mName;
	mActive = pState.mActive;

	mStateEffects.clear();
	for (auto effect : pState.mStateEffects)
	{
		mStateEffects.push_back(std::shared_ptr<StateEffect>(new StateEffect(*effect)));
	}

	mSubStates.clear();
	for (auto subState : pState.mSubStates)
	{
		mSubStates.push_back(std::shared_ptr<State>(new State(*subState)));
	}

	return *this;
}

const std::string& 
State::name() const
{
	return mName;
}

bool
State::active() const
{
	return mActive;
}

const std::vector<std::shared_ptr<StateEffect>>& 
State::stateEffects() const
{
	return mStateEffects;
}

std::shared_ptr<State> 
State::parentState() const
{
	return mParentState;
}

const std::vector<std::shared_ptr<State>>& 
State::subStates() const
{
	return mSubStates;
}

void 
State::setStateName(const std::string& pStateName)
{
	mName = pStateName;
}

void 
State::setActive(bool pActive, bool pIncludeSubStates)
{
	std::cout << "State " << mName << " setActive " << pActive << "\n";

	mActive = pActive;

	if (pIncludeSubStates == true)
	{
		for (auto _state : mSubStates)
		{
			_state->setActive(mActive);
		}
	}
}
	
void 
State::addStateEffect(const StateEffect& pStateEffect)
{
	mStateEffects.push_back( std::shared_ptr<StateEffect>( new StateEffect(pStateEffect)));
}

void 
State::addSubState(const State& pSubState)
{
	// TODO: no parent state is set for substate, this needs to be done from outside for instance by the StateMachine class

	std::shared_ptr<State> _subState(new State(pSubState));
	mSubStates.push_back(_subState);
}

void 
State::addSubState(std::shared_ptr<State>& pSubState)
{
	mSubStates.push_back(pSubState);
}

void 
State::setParentState(std::shared_ptr<State>& pParentState)
{
	mParentState = pParentState;
}

const std::vector<std::shared_ptr<StateTransition> >& 
State::incomingStateTransitions() const
{
	return mIncomingStateTransitions;
}

const std::vector<std::shared_ptr<StateTransition> >& 
State::outgoingStateTransitions() const
{
	return mOutgoingStateTransitions;
}

void 
State::addIncomingStateTransition(std::shared_ptr<StateTransition> pTransition)
{
	mIncomingStateTransitions.push_back(pTransition);
}

void 
State::addOutgoingStateTransition(std::shared_ptr<StateTransition> pTransition)
{
	mOutgoingStateTransitions.push_back(pTransition);
}

void 
State::changeBodies(const std::vector<std::string>& pBodyNames, bool pIncludeSubStates)
{
	for (auto stateEffect : mStateEffects)
	{
		stateEffect->changeBodies(pBodyNames);
	}

	if (pIncludeSubStates == true)
	{
		for (auto subState : mSubStates)
		{
			subState->changeBodies(pBodyNames);
		}
	}
}

void 
State::changeBodies(const std::vector<std::string>& pBodyNames, StateEffectType pEffectType, bool pIncludeSubStates)
{
	for (auto stateEffect : mStateEffects)
	{
		if (stateEffect->effectType() == pEffectType) stateEffect->changeBodies(pBodyNames);
	}

	if (pIncludeSubStates == true)
	{
		for (auto subState : mSubStates)
		{
			subState->changeBodies(pBodyNames, pEffectType, pIncludeSubStates);
		}
	}
}

void 
State::changeBodies(const std::vector<std::string>& pBodyNames, StateEffectType pEffectType, const std::string& pParameterName, bool pIncludeSubStates)
{
	for (auto stateEffect : mStateEffects)
	{
		if (stateEffect->effectType() == pEffectType && stateEffect->parameterName() == pParameterName) stateEffect->changeBodies(pBodyNames);
	}

	if (pIncludeSubStates == true)
	{
		for (auto subState : mSubStates)
		{
			subState->changeBodies(pBodyNames, pEffectType, pParameterName, pIncludeSubStates);
		}
	}
}


void 
State::changeTargets(const std::vector<std::string>& pTargetNames, bool pIncludeSubStates)
{
	for (auto stateEffect : mStateEffects)
	{
		stateEffect->changeTargets(pTargetNames);
	}

	if (pIncludeSubStates == true)
	{
		for (auto subState : mSubStates)
		{
			subState->changeTargets(pTargetNames, pIncludeSubStates);
		}
	}
}

void 
State::changeTargets(const std::vector<std::string>& pTargetNames, StateEffectType pEffectType, bool pIncludeSubStates)
{
	for (auto stateEffect : mStateEffects)
	{
		if (stateEffect->effectType() == pEffectType)
		{
			stateEffect->changeTargets(pTargetNames);
		}
	}

	if (pIncludeSubStates == true)
	{
		for (auto subState : mSubStates)
		{
			subState->changeTargets(pTargetNames, pEffectType, pIncludeSubStates);
		}
	}
}

void
State::changeTargets(const std::vector<std::string>& pTargetNames, StateEffectType pEffectType, const std::string& pParameterName, bool pIncludeSubStates)
{
	for (auto stateEffect : mStateEffects)
	{
		if (stateEffect->effectType() == pEffectType && stateEffect->parameterName() == pParameterName)
		{
			stateEffect->changeTargets(pTargetNames);
		}
	}

	if (pIncludeSubStates == true)
	{
		for (auto subState : mSubStates)
		{
			subState->changeTargets(pTargetNames, pEffectType, pParameterName, pIncludeSubStates);
		}
	}
}


void 
State::changeParameterName(const std::string& pParameterName)
{
	for (auto stateEffect : mStateEffects)
	{
		stateEffect->changeParameterName(pParameterName);
	}

	for (auto subState : mSubStates)
	{
		subState->changeParameterName(pParameterName);
	}
}

void 
State::changeParameterValue(const std::string& pParameterName, const AbstractValue& pParameterValue, bool pIncludeSubStates)
{
	for (auto stateEffect : mStateEffects)
	{
		if (stateEffect->parameterName() == pParameterName)
		{
			stateEffect->changeParameterValue(pParameterValue);
		}
	}

	if (pIncludeSubStates == true)
	{
		for (auto subState : mSubStates)
		{
			subState->changeParameterValue(pParameterName, pParameterValue, pIncludeSubStates);
		}
	}
}

void 
State::changeParameterValue(const std::vector<std::string>& pTargetNames, const std::string& pParameterName, const AbstractValue& pParameterValue, bool pIncludeSubStates)
{
	for (auto stateEffect : mStateEffects)
	{
		if (stateEffect->targetNames() == pTargetNames && stateEffect->parameterName() == pParameterName)
		{
			stateEffect->changeParameterValue(pParameterValue);
		}
	}

	if (pIncludeSubStates == true)
	{
		for (auto subState : mSubStates)
		{
			subState->changeParameterValue(pTargetNames, pParameterName, pParameterValue, pIncludeSubStates);
		}
	}
}

void
State::update() throw(dab::Exception)
{
	if (mActive == false) return;

	//std::cout << "State " << mName << " update\n";

	for (auto subState : mSubStates)
	{
		subState->update();
	}

	for (auto stateTransition : mOutgoingStateTransitions)
	{
		stateTransition->update();

		//std::cout << "transition ready " << stateTransition->ready() << "\n";

		if (stateTransition->ready() == true)
		{
			std::shared_ptr<State> _nextState = stateTransition->apply();

			if (_nextState != nullptr)
			{
				_nextState->setActive(true);
				_nextState->apply();

				setActive(false);
			}

			break;
		}
	}
}

void 
State::apply() throw(dab::Exception)
{
	if (mActive == false) return;

	for (auto subState : mSubStates)
	{
		subState->apply();
	}

	std::cout << "State " << mName << " apply\n";

	for (auto stateEffect : mStateEffects)
	{
		stateEffect->apply();
	}

	for (auto stateTransition : mOutgoingStateTransitions)
	{
		stateTransition->reset();
	}
}

State::operator std::string() const
{
	return info();
}

std::string
State::info() const
{
	std::stringstream ss;

	ss << "state name: " << mName << "\n";
	for (auto stateEffect : mStateEffects) ss << "state effect:\n" << *stateEffect << "\n";
	for (auto subState : mSubStates) ss << "substate\n" << *subState << "\n";

	return ss.str();
}

# pragma mark StateTransitionCondition definition

StateTransitionCondition::StateTransitionCondition()
	: mReady(false)
{}

StateTransitionCondition::StateTransitionCondition(const StateTransitionCondition& pCondition)
	: mReady(pCondition.mReady)
{}

const StateTransitionCondition& 
StateTransitionCondition::operator=(const StateTransitionCondition& pCondition)
{
	mReady = pCondition.mReady;
	return *this;
}

std::shared_ptr<StateTransitionCondition> 
StateTransitionCondition::copy() const
{
	return std::shared_ptr<StateTransitionCondition>( new StateTransitionCondition(*this) );
}

bool
StateTransitionCondition::ready() const
{
	return mReady;
}

void
StateTransitionCondition::setReady(bool pReady)
{
	mReady = pReady;
}

void
StateTransitionCondition::update()
{
	//std::cout << "StateTransitionCondition::update\n";
}

void 
StateTransitionCondition::reset()
{
	mReady = false;
}


# pragma mark StateTransitionTimed definition

StateTransitionTimed::StateTransitionTimed(double pDuration)
	: mDuration(pDuration)
{
	mResetTime = ofGetElapsedTimef();
}

StateTransitionTimed::StateTransitionTimed(const StateTransitionTimed& pCondition)
	: StateTransitionCondition(pCondition)
	, mDuration(pCondition.mDuration)
	, mResetTime(pCondition.mResetTime)
{}


const StateTransitionTimed& 
StateTransitionTimed::operator=(const StateTransitionTimed& pCondition)
{
	StateTransitionCondition::operator=(pCondition);
	mDuration = pCondition.mDuration;
	mResetTime = pCondition.mResetTime;
	return *this;
}

std::shared_ptr<StateTransitionCondition>
StateTransitionTimed::copy() const
{
	return std::shared_ptr<StateTransitionTimed>(new StateTransitionTimed(*this));
}

void
StateTransitionTimed::update()
{
	double currentTime = ofGetElapsedTimef();
	if ((currentTime - mResetTime) >= mDuration) mReady = true;

	//std::cout << "StateTransitionTimed::update: reset time " << mResetTime << " currentTime " << currentTime << " duration " << mDuration << " ready " << mReady << "\n";
}

void
StateTransitionTimed::reset()
{
	StateTransitionCondition::reset();
	mResetTime = ofGetElapsedTimef();
}

# pragma mark StateTransition definition

StateTransition::StateTransition(std::shared_ptr<State> pPreviousState, std::vector<std::shared_ptr<State>> pNextStates, const StateTransitionCondition& pCondition)
	: mPreviousState(pPreviousState)
	, mNextStates(pNextStates)
	, mTransitionCondition(pCondition.copy())
{
	//std::cout << "StateTransition::StateTransition " << this << " from: " << pPreviousState->name() << " to: ";
	//for (auto nextState : pNextStates) std::cout << nextState->name() << " ";
	//std::cout << "condition " << mTransitionCondition << "\n";

	setProbabilities(std::vector<float>(mNextStates.size(), 1.0 / static_cast<float>(mNextStates.size())));
}

void 
StateTransition::setProbabilities(const std::vector<float>& pProbabilties)
{
	int nextStateCount = mNextStates.size();
	std::vector<float> _probabilities = pProbabilties;
	if (_probabilities.size() != nextStateCount) _probabilities.resize(nextStateCount, 0.0);

	float totalProb = 0.0;
	for (float p : _probabilities) totalProb += p;
	for (int pI = 0; pI < nextStateCount; ++pI) _probabilities[pI] /= totalProb;

	mNextStateProbabilities = _probabilities;
}

bool 
StateTransition::ready()
{
	return mTransitionCondition->ready();
}

void 
StateTransition::reset()
{
	mTransitionCondition->reset();
}

void 
StateTransition::update()
{
	mTransitionCondition->update();
}

std::shared_ptr<State>
StateTransition::apply()
{
	std::shared_ptr<State> _nextState(nullptr);

	int nextStateCount = mNextStates.size();
	if (nextStateCount == 1)
	{
		_nextState = mNextStates[0];
	}
	else
	{
		float rand = ofRandom(1.0);
		float cumRand = 0.0;

		for (int sI = 0; sI < nextStateCount; ++sI)
		{
			cumRand += mNextStateProbabilities[sI];
			if (rand <= cumRand)
			{
				_nextState = mNextStates[sI];
				break;
			}
		}
	}

	if (_nextState == nullptr) std::cout << "Alarm: nextState is null\n";

	if (_nextState != nullptr)
	{
		_nextState->apply();
		mTransitionCondition->reset();
	}

	return _nextState;
}

# pragma mark StateMachine definition

StateMachine::StateMachine()
	: mPaused(false)
{}

void 
StateMachine::addState(std::shared_ptr<State> pState)
{
	mStates.push_back(pState);
}

void 
StateMachine::start()
{
	if (isThreadRunning() == false)
	{
		mTime = ofGetElapsedTimef();
		startThread();
	}
}

void 
StateMachine::stop()
{
	if (isThreadRunning() == true) stopThread();
}

bool 
StateMachine::paused() const
{
	return mPaused;
}

void 
StateMachine::setPaused(bool pPaused)
{
	mPaused = pPaused;
}

void 
StateMachine::update()
{
	for (auto _state : mStates)
	{
		if (_state->parentState() == nullptr && _state->active() == true) _state->update();
	}
}

void 
StateMachine::threadedFunction()
{
	while (isThreadRunning())
	{
		if (mPaused == false)
		{
			double currentTime = ofGetElapsedTimef();
			if (currentTime - mTime < mUpdateInterval) continue;
			else mTime = currentTime;

			update();
		}

		std::this_thread::sleep_for(std::chrono::microseconds(10));
	}
}


# pragma mark StateManager definition

StateManager::StateManager()
{
	init();
}

std::shared_ptr<State> 
StateManager::state(const std::string& pStateName) const throw (dab::Exception)
{
	if (mStates.find(pStateName) == mStates.end()) throw dab::Exception("Physics Error: state with name " + pStateName + " not found", __FILE__, __FUNCTION__, __LINE__);

	return mStates.at(pStateName);
}

std::shared_ptr<State> 
StateManager::createState(const std::string& pStateName) throw (dab::Exception)
{
	if (mStates.find(pStateName) != mStates.end()) throw dab::Exception("Physics Error: state with name " + pStateName + " already exists", __FILE__, __FUNCTION__, __LINE__);

	std::shared_ptr<State> _state( new State(pStateName) );
	mStates[pStateName] = _state;

	return _state;
}

std::shared_ptr<State> 
StateManager::loadState(const std::string& pStateName, const std::string& pPresetFileName, int pPresetNr, const std::string& pPresetMapName) throw (dab::Exception)
{
	if (mStates.find(pStateName) == mStates.end()) throw dab::Exception("Physics Error: state with name " + pStateName + " not found", __FILE__, __FUNCTION__, __LINE__);

	std::shared_ptr<State> _state = mStates[pStateName];

	try
	{
		dab::physics::StateSerialize& serialize = dab::physics::StateSerialize::get();
		serialize.loadStateFromMaxPreset(*_state, pPresetFileName, pPresetNr, pPresetMapName);
	}
	catch(dab::Exception& e)
	{ 
		e += dab::Exception("Physics Error: failed to load state " + pStateName + " from preset file " + pPresetFileName + " with preset nr " + std::to_string(pPresetNr), __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}

	return _state;
}

std::shared_ptr<State> 
StateManager::copyState(const std::string& pSourceStateName) throw (dab::Exception)
{
	if (mStates.find(pSourceStateName) == mStates.end()) throw dab::Exception("Physics Error: state with name " + pSourceStateName + " not found", __FILE__, __FUNCTION__, __LINE__);

	std::shared_ptr<State> _sourceState = mStates[pSourceStateName];
	std::shared_ptr<State> _targetState(new State(*_sourceState));

	return _targetState;
}

std::shared_ptr<State> 
StateManager::copyState(const std::string& pSourceStateName, const std::string& pTargetStateName) throw (dab::Exception)
{
	if (mStates.find(pSourceStateName) == mStates.end()) throw dab::Exception("Physics Error: state with name " + pSourceStateName + " not found", __FILE__, __FUNCTION__, __LINE__);
	if (mStates.find(pTargetStateName) != mStates.end()) throw dab::Exception("Physics Error: state with name " + pTargetStateName + " already exists", __FILE__, __FUNCTION__, __LINE__);

	std::shared_ptr<State> _sourceState = mStates[pSourceStateName];
	std::shared_ptr<State> _targetState(new State(*_sourceState));
	_targetState->setStateName(pTargetStateName);

	mStates[pTargetStateName] = _targetState;

	return _targetState;
}

std::shared_ptr<State> 
StateManager::addSubState(const std::string& pParentStateName, const std::string& pSubStateName) throw (dab::Exception)
{
	if (mStates.find(pParentStateName) == mStates.end()) throw dab::Exception("Physics Error: state with name " + pParentStateName + " not found", __FILE__, __FUNCTION__, __LINE__);
	if (mStates.find(pSubStateName) == mStates.end()) throw dab::Exception("Physics Error: state with name " + pSubStateName + " not found", __FILE__, __FUNCTION__, __LINE__);

	std::shared_ptr<State> _parentState = mStates[pParentStateName];
	std::shared_ptr<State> _subState = mStates[pSubStateName];

	_parentState->addSubState(_subState);
	_subState->setParentState(_parentState);

	return _subState;
}

void 
StateManager::init()
{
	createDefaultStates();
}

void 
StateManager::createDefaultStates()
{
	try
	{
		// create Physics state
		std::shared_ptr<State> _physicsState = createState("Physics");
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyPartEffect, {}, {}, "mass", dab::Value<float>(0.0)));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyPartEffect, {}, {}, "linearDamping", dab::Value<float>(0.0)));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyPartEffect, {}, {}, "angularDamping", dab::Value<float>(0.0)));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyPartEffect, {}, {}, "friction", dab::Value<float>(0.0)));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyPartEffect, {}, {}, "rollingFriction", dab::Value<float>(0.0)));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyPartEffect, {}, {}, "restitution", dab::Value<float>(0.0)));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "bounce", dab::Value<float>(0.0)));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "damping", dab::Value<float>(0.0)));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularActive", dab::Value<std::array<bool, 3>>({ false, false, false })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularLowerLimit", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularUpperLimit", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularStopERP", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularStopCFM", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "maxAngularMotorForce", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularVelocity", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularServoActive", dab::Value<std::array<bool, 3>>({ false, false, false })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularServoTarget", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularSpringActive", dab::Value<std::array<bool, 3>>({ false, false, false })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularSpringStiffness", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularSpringDamping", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_physicsState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "angularSpringRestLength", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));

		// create SpeedBehavior state
		std::shared_ptr<State> _speedState = createState("SpeedBehavior");
		_speedState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "active", dab::Value<bool>(false)));
		_speedState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "speed", dab::Value<float>(0.0)));
		_speedState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "amount", dab::Value<float>(0.0)));

		// create RandomForceBehavior state
		std::shared_ptr<State> _randomForceState = createState("RandomForceBehavior");
		_randomForceState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "active", dab::Value<bool>(false)));
		_randomForceState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "minDir", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_randomForceState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "maxDir", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_randomForceState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "minAmp", dab::Value<float>(0.0)));
		_randomForceState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "maxAmp", dab::Value<float>(0.0)));
		_randomForceState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "appInterval", dab::Value<float>(1.0)));
		_randomForceState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "randInterval", dab::Value<float>(1.0)));

		// create RandomTorqueBehavior state
		std::shared_ptr<State> _randomTorqueState = createState("RandomTorqueBehavior");
		_randomTorqueState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "active", dab::Value<bool>(false)));
		_randomTorqueState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "minTorque", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_randomTorqueState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "maxTorque", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_randomTorqueState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "scale", dab::Value<float>(0.0)));
		_randomTorqueState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "appInterval", dab::Value<float>(1.0)));
		_randomTorqueState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "randInterval", dab::Value<float>(1.0)));

		// create RandomRotationTargetBehavior state
		std::shared_ptr<State> _randomRotationTargetState = createState("RandomRotationTargetBehavior");
		_randomRotationTargetState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "active", dab::Value<bool>(false)));
		_randomRotationTargetState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "minTarget", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_randomRotationTargetState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "maxTarget", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 })));
		_randomRotationTargetState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "speed", dab::Value<float>(0.0)));
		_randomRotationTargetState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "appInterval", dab::Value<float>(1.0)));
		_randomRotationTargetState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "randInterval", dab::Value<float>(1.0)));

		// create VolumeBehavior state
		std::shared_ptr<State> _volumeState = createState("VolumeBehavior");
		_volumeState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "active", dab::Value<bool>(false)));
		_volumeState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "maxDist", dab::Value<float>(10.0)));
		_volumeState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "minAmp", dab::Value<float>(0.0)));
		_volumeState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "maxAmp", dab::Value<float>(0.0)));
		_volumeState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "appInterval", dab::Value<float>(1.0)));

		// create CohesionBehavior state
		std::shared_ptr<State> _cohesionState = createState("CohesionBehavior");
		_cohesionState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "active", dab::Value<bool>(false)));
		_cohesionState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "minDist", dab::Value<float>(0.0)));
		_cohesionState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "maxDist", dab::Value<float>(10.0)));
		_cohesionState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "amount", dab::Value<float>(0.0)));

		// create AlignmentBehavior state
		std::shared_ptr<State> _alignmentState = createState("AlignmentBehavior");
		_alignmentState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "active", dab::Value<bool>(false)));
		_alignmentState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "minDist", dab::Value<float>(0.0)));
		_alignmentState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "maxDist", dab::Value<float>(10.0)));
		_alignmentState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "linearAmount", dab::Value<float>(0.0)));
		_alignmentState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "angularAmount", dab::Value<float>(0.0)));
		_alignmentState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "amount", dab::Value<float>(0.0)));
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to create default states", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}
}

std::shared_ptr<StateTransition> 
StateManager::createStateTransition(const std::string& pPreviousStateName, const std::vector<std::string>& pNextStateNames, const StateTransitionCondition& pCondition) throw (dab::Exception)
{
	try
	{
		std::shared_ptr<State> _previousState = state(pPreviousStateName);
		std::vector<std::shared_ptr<State>> _nextStates;
		for (auto nextStateName : pNextStateNames)
		{
			std::shared_ptr<State> _nextState = state(nextStateName);
			_nextStates.push_back(_nextState);
		}

		std::shared_ptr<StateTransition> _stateTransition( new StateTransition(_previousState, _nextStates, pCondition));
		_previousState->addOutgoingStateTransition(_stateTransition);
		for (auto _nextState : _nextStates)
		{
			_nextState->addIncomingStateTransition(_stateTransition);
		}

		return _stateTransition;
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to create state transition", __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}
}

std::shared_ptr<State> 
StateManager::loadState(std::shared_ptr<State> pState, const std::string& pPresetFileName, int pPresetNr, const std::string& pPresetMapName) throw (dab::Exception)
{
	try
	{
		dab::physics::StateSerialize& serialize = dab::physics::StateSerialize::get();
		serialize.loadStateFromMaxPreset(*pState, pPresetFileName, pPresetNr, pPresetMapName);
	}
	catch (dab::Exception& e)
	{
		e += dab::Exception("Physics Error: failed to load state " + pState->name() + " from preset file " + pPresetFileName + " with preset nr " + std::to_string(pPresetNr), __FILE__, __FUNCTION__, __LINE__);
		throw e;
	}

	return pState;
}

std::shared_ptr<State> 
StateManager::copyState(std::shared_ptr<State> pSourceState)
{

	std::shared_ptr<State> _targetState(new State(*pSourceState));
	return _targetState;
}

std::shared_ptr<State> 
StateManager::addSubState(std::shared_ptr<State> pParentState, std::shared_ptr<State> pSubState)
{
	pParentState->addSubState(pSubState);
	pSubState->setParentState(pParentState);

	return pSubState;
}

std::shared_ptr<StateTransition> 
StateManager::createStateTransition(std::shared_ptr<State> pPreviousState, const std::vector<std::shared_ptr<State>>& pNextStates, const StateTransitionCondition& pCondition)
{
	std::shared_ptr<StateTransition> _stateTransition(new StateTransition(pPreviousState, pNextStates, pCondition));
	pPreviousState->addOutgoingStateTransition(_stateTransition);
	for (auto _nextState : pNextStates)
	{
		_nextState->addIncomingStateTransition(_stateTransition);
	}

	return _stateTransition;
}
