import discord
from typing import List, Dict, Tuple

class DayView(discord.ui.View):
    def __init__(self, question_id: int, responses: List[Dict[str, str]], correct_response: str):
        super().__init__()
        self.question_id = question_id
        self.responses = responses
        self.correct_response = correct_response
        self.user_responses = {}
        self.correct_responses = set()
        self.incorrect_responses = set()
        for response in responses:
            print(f"Adding button for response: {response['response_text']} with ID: {response}")
            btn = discord.ui.Button(label=response["response_text"], style=discord.ButtonStyle.secondary, custom_id=f"response_{response['id']}")
            btn.callback = self.button_callback
            self.add_item(btn)
            
    async def button_callback(self, interaction: discord.Interaction):
            if interaction.user.id in self.user_responses:
                await interaction.response.send_message("You have already responded to this question.", ephemeral=True)
                return
            self.user_responses[interaction.user.id] = interaction.data['custom_id']
            if interaction.data['custom_id'] == f"response_{self.correct_response['id']}":
                self.correct_responses.add(interaction.user.id)
                await interaction.response.send_message("Correct!", ephemeral=True)
            else:
                self.incorrect_responses.add(interaction.user.id)
                await interaction.response.send_message(f"Incorrect! Response was {self.correct_response['response_text']}", ephemeral=True)
            await interaction.response.send_message(f"You selected: {interaction.data['custom_id']}", ephemeral=True)
    
    def count_responses(self):
        return len(self.correct_responses), len(self.incorrect_responses)
    