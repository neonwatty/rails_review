require "application_system_test_case"

class DeviseAuthSystemTest < ApplicationSystemTestCase

  test 'test_1: sign in existing user (from seed)' do
    # set to homepage and see if 'Log in' link is present
    visit root_path
    assert_link "Log in", href: new_user_session_path

    # visit login page and fill in form
    visit new_user_session_path
    assert_selector '#new_user'
    fill_in 'user_email', with: 'neonwatty@gmail.com'
    fill_in 'user_password', with: 'password123'
    click_on 'new-session-login-btn'
    assert_current_path root_path

    # confirm login - 'Log in' link should not be present
    assert_no_link "Log in", href: new_user_session_path

    # log out and confirm 'Log in' link is present
    click_on 'Log out'
    assert_current_path root_path
    assert_link "Log in", href: new_user_session_path
  end

  test 'test_2: sign up' do
    # set to homepage and see if 'Log in' link is present
    visit root_path
    assert_link "Log in", href: new_user_session_path
    assert_link "Sign up", href: new_user_registration_path

    # visit signup page and fill in form
    visit new_user_registration_path
    fill_in 'user_email', with: 'dummy@dummy.com'
    fill_in 'user_password', with: 'password'
    fill_in 'user_password_confirmation', with: 'password'
    click_on 'signup-registration-btn'
    assert_current_path root_path
  end

end
  