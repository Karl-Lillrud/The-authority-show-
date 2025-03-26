import { showNotification } from "./notifications.js"
import { updateTeamsUI } from "./teamUI.js"
import {
  addTeamRequest,
  getTeamsRequest,
  editTeamRequest,
  deleteTeamRequest,
  updatePodcastTeamRequest,
} from "/static/requests/teamRequests.js"

export async function addTeam(payload) {
  try {
    const response = await addTeamRequest(payload)
    showNotification("Success", "Team successfully created!", "success")
    const teams = await getTeamsRequest()
    updateTeamsUI(teams)
    return response
  } catch (error) {
    console.error("Error adding team:", error)
    showNotification("Error", "Failed to create team.", "error")
    throw error
  }
}

export async function deleteTeam(teamId) {
  try {
    const result = await deleteTeamRequest(teamId)
    if (result.message) {
      showNotification("Success", result.message || "Team deleted successfully!", "success")
      const teams = await getTeamsRequest()
      updateTeamsUI(teams)
      return result
    } else {
      showNotification("Error", result.error || "Failed to delete team.", "error")
      throw new Error(result.error || "Failed to delete team")
    }
  } catch (error) {
    console.error("Error deleting team:", error)
    showNotification("Error", "An error occurred while deleting the team.", "error")
    throw error
  }
}

export async function saveTeamDetails(teamId, payload) {
  try {
    const result = await editTeamRequest(teamId, payload)
    if (result.message) {
      showNotification("Success", result.message || "Team updated successfully!", "success")
      const teams = await getTeamsRequest()
      updateTeamsUI(teams)
      return result
    } else {
      showNotification("Error", result.error || "Failed to update team.", "error")
      throw new Error(result.error || "Failed to update team")
    }
  } catch (error) {
    console.error("Error updating team:", error)
    showNotification("Error", "An error occurred while updating the team.", "error")
    throw error
  }
}

export async function updatePodcastTeam(podcastId, teamId) {
  try {
    const updateResponse = await updatePodcastTeamRequest(podcastId, {
      teamId: teamId || "",
    })
    return updateResponse
  } catch (error) {
    console.error("Error updating podcast team:", error)
    showNotification("Error", "An error occurred while updating the podcast team.", "error")
    throw error
  }
}

