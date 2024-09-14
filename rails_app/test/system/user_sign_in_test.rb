require 'test_helper'

class UserSignInTest < ActionDispatch::SystemTestCase
  driven_by :selenium_chrome_headless
  fixtures :all  

  def setup
    @user = users(:one)  
  end

  test 'test_1: existing user can sign in' do
    visit new_user_session_path

    fill_in 'Email', with: @user.email
    fill_in 'Password', with: 'password123'
    click_button 'Log in'

    assert_text 'Signed in successfully.'
    assert_current_path root_path
  end

  test 'test_2: non-existing user cannot sign in' do
    visit new_user_session_path

    # invalid sign in
    fill_in 'Email', with: "not an email"
    fill_in 'Password', with: 'a non user email'
    click_button 'Log in'
    assert_current_path new_user_session_path 

    # non-existing sign in
    fill_in 'Email', with: "not_a_user@email.com"
    fill_in 'Password', with: 'a non user email'
    click_button 'Log in'
    assert_current_path new_user_session_path 
  end
end
