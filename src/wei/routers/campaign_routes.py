"""
Router for the "campaigns" endpoints
"""

from typing import Dict

from fastapi import APIRouter

from wei.core.events import EventHandler
from wei.core.state_manager import state_manager
from wei.types.event_types import CampaignStartEvent
from wei.types.experiment_types import Campaign, CampaignDesign

router = APIRouter()


@router.post("/")
def register_campaign(campaign_design: CampaignDesign) -> Campaign:
    """Creates a new campaign

    Parameters
    ----------
    campaign_design: CampaignDesign
        The design of a new campaign to register
    Returns
    -------
    response: Campaign
        The registered campaign
    """

    campaign = Campaign.model_validate(campaign_design, from_attributes=True)
    state_manager.set_campaign(campaign)
    EventHandler.log_event(CampaignStartEvent(campaign=campaign))
    return campaign


@router.get("/")
@router.get("/all")
def get_all_campaigns() -> Dict[str, Campaign]:
    """Returns all campaigns"""
    return state_manager.get_all_campaigns()


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str) -> Campaign:
    """Returns the details of a campaign"""
    return state_manager.get_campaign(campaign_id)
